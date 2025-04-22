# ライブラリのインポート
import os
import io
import json
from typing import List, Union
import ftfy, html, re
import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer, AutoImageProcessor, BatchFeature
import psycopg2
from psycopg2.extras import DictCursor
from streamlit.runtime.uploaded_file_manager import UploadedFile
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

IMAGES_PER_PAGE = 2 # 1ページあたりの画像数

# PostgreSQLデータベースへの接続
def get_connection():
    return psycopg2.connect(
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )

#  Japanese Stable CLIPモデルのロード
device = "cuda" if torch.cuda.is_available() else "cpu"
model_path = "stabilityai/japanese-stable-clip-vit-l-16"
model = AutoModel.from_pretrained(model_path, trust_remote_code=True).eval().to(device)
tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
processor = AutoImageProcessor.from_pretrained(model_path, use_fast=True)

# テキストをクリーンアップする関数
def basic_clean(text):
    text = ftfy.fix_text(text)
        # ftfy(Fix Text For You): テキストの文字化けや間違ったエンコーディングを修正するライブラリ
    text = html.unescape(html.unescape(text))
        # html.unescape: HTMLエンティティ(ex: &amp;, &lt;, &gt;, &#39; など)を変換する
        # 二重エンコードの場合に対応するため、2回実行している
    return text.strip()
        # strip: 文字列の先頭と末尾の空白文字を削除する

# テキスト内の余分な空白文字を削除する関数
def whitespace_clean(text):
    text = re.sub(r"\s+", " ", text)
        # re.sub: 正規表現にマッチする部分を置換する
        # r"\s+": 1つ以上の空白文字にマッチする正規表現
        # " ": 置換後の文字列(1つの空白文字に置換)
    text = text.strip()
    return text

# テキストをトークン化する関数
def tokenize(texts: Union[str, List[str]], max_seq_len: int=77):
    """
    テキストをトークン化する関数
    
    Args:
        texts(Union[str, List[str]]): トークン化するテキスト
        max_seq_len(int): 最大シーケンス長

    Returns:
        BatchFeature: トークン化されたテキスト
    """
    # 入力をリスト形式で統一
    if isinstance(texts, str):
        texts = [texts]
    texts = [whitespace_clean(basic_clean(text)) for text in texts]

    # テキストをトークン化
    inputs = tokenizer(
        texts,
        max_length=max_seq_len-1, # 最大長(BOSトークを追加するため1つ短く)
        padding="max_length", # すべてのシーケンスを同じ長さにパディング
        truncation=True, # 長すぎるテキストはmax_seq_len-1に切り捨て
        add_special_tokens=False # BOSなどの特殊トークンをこの段階では追加しない
    )
        # tokenizerの出力 
            # inputs["input_ids"]  # 例: [[23, 45, 678, 90, 4, 5, ...]]
                # 各単語を対応するトークンIDに変換したもの
            # inputs["attention_mask"]  # 例: [[1, 1, 1, 1, 1, 0, 0, ...]]
                # 1(注意を払う), 0(無視:パディング)のマスク
        # トークンIDは, モデルのボキャブラリー内の単語に対応する(訓練済み)

    inputs_ids = [[tokenizer.bos_token_id] + ids for ids in inputs["input_ids"]]
        # BOS(Begging of Sentence)トークンを追加
            # BOSトークン: モデルが文の開始を示すために使用する特殊トークン
    attention_mask = [[1] + am for am in inputs["attention_mask"]]
        # [1]: BOSトークンに対応するマスクを追加
        #  パディング部分(0)と実際のトークン(1)を区別するためのマスク
    position_ids = [list(range(0, len(inputs_ids[0])))] * len(texts)

    return BatchFeature(
        {
            "input_ids": torch.tensor(inputs_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "position_ids": torch.tensor(position_ids, dtype=torch.long)
        }
    )
        # BatchFeature: Hugging FaceのTokenizerがバッチデータを扱うためのクラス
        
# テキストの埋め込みベクトルを計算する関数
def compute_text_embeddings(text):
    """
    テキストの埋め込みベクトルを計算する関数

    Args:
        text(str): 埋め込みを計算するテキスト

    Returns:
        torch.Tensor: 正規化されたテキストの埋め込みベクトル
    """
    # 入力textが単一の文字列の場合、単一要素のリストに変換し、複数の文字列を要素に持つリストの場合はそのまま、後続のステップへ渡す
    # -> 複数のテキストを一度に処理できるようになる(今回の作例では不要だが、事前に複数のテキストベクトルを生成しておく必要のある分類タスクなどで有用)
    if isinstance(text, str):
        text = [text]
        
    # テキストをモデルが理解できる形式(トークン)に変換
    text = tokenize(texts=text)
    
    # トークン化されたテキストからテキスト特徴量(ベクトル)を抽出
    text_features = model.get_text_features(**text.to(device))
    
    # 抽出された特徴量ベクトルをL2ノルムで正規化
    text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
    
    # 不要になったテキストデータの削除
    del text
    return text_features.cpu().detach()

# 画像の埋め込みベクトルを計算する関数
def compute_image_embeddings(image):
    """
    画像の埋め込みベクトルを計算する関数

    Args:
        image(PIL.Image.Image): 埋め込みを計算する画像

    Returns:
        torch.Tensor: 正規化された画像の埋め込みベクトル
    """
		# 入力画像をモデルが受け入れ可能な形式に前処理する
    image = processor(images=image, return_tensors="pt").to(device)
	    # return_tensors="pt": PyTorchのテンソルを返すようにしている
	    
    # 学習時にだけ必要な勾配計算を無効にし、メモリ使用量を減らし、計算を高速化
    with torch.no_grad():
        image_features = model.get_image_features(**image) # 画像の特徴ベクトルを抽出
        
    # 画像の特徴ベクトルをL2正規化する(これにより、ベクトルの長さが1になる)
    image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
	    # 2つのベクトルの比較をする際に、コサイン類似度の計算を容易にする(計算が内積だけになる)
	    # 異なる画像間の比較を公平にする
    return image_features.cpu().detach()

def get_image_data(image_id):
    """
    画像データを取得する関数

    Args:
        image_id(int): 画像ID

    Returns:
        dict: 画像データ
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                "SELECT image_data FROM images WHERE image_id = %s",
                (image_id,)
            )
            row = cur.fetchone()
    return row["image_data"] if row else None

def get_multiple_image_data(image_ids):
    """
    複数の画像データを取得する関数

    Args:
        image_ids(List[int]): 画像IDのリスト

    Returns:
        dict: 画像データの辞書
    """
    if not image_ids:
        return {}
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                "SELECT image_id, image_data FROM images WHERE image_id = ANY(%s)",
                (image_ids,)
            )
            rows = cur.fetchall()
    return {row["image_id"]: row["image_data"] for row in rows}

def load_initial_images(page=1):
    """
    対象ページの画像と画像情報を取得する関数
    
    Args:
        page(int): ページ番号

    Returns:
        Tuple[List[PIL.Image.Image], List[dict]]: 画像と画像情報のリスト
    """
    # ページ番号からオフセットを計算
    offset = (page - 1) * IMAGES_PER_PAGE

    # 最新の画像データを取得
    results = get_latest_images(limit=IMAGES_PER_PAGE, offset=offset)

    # 画像データを取得
    image_ids = [result["image_id"] for result in results]
    image_data_dict = get_multiple_image_data(image_ids)

    images = []
    image_info = []

    # 画像データと画像情報をリストに追加
    for result in results:
        image_data = image_data_dict.get(result["image_id"])
        if image_data:
            images.append(Image.open(io.BytesIO(image_data)))
                # io.BytesIO: バイナリデータをメモリ上のファイルのように扱えるストリームオブジェクトに変換
                # Image.open: ストリームオブジェクトから画像を開く
            image_info.append({
                "file_name": result["file_name"],
                "vector_distance": "N/A"
            })

    return images, image_info

def get_latest_images(limit=16, offset=0):
    """
    最新の画像データを取得する関数

    Args:
        limit(int): 取得する画像の数
        offset(int): オフセット

    Returns:
        List[dict]: 画像データのリスト
    """
    query = """
        SELECT image_id, file_name
        FROM images
        ORDER BY upload_date DESC
        LIMIT %s OFFSET %s
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(query, (limit, offset))
            rows = cur.fetchall()

    return [{
        "image_id": row["image_id"],
        "file_name": row["file_name"]
    } for row in rows]

def search_images(query, search_method):
    query_str = """
            SELECT i.image_id, i.file_name,
            cie.embedding <#> %s as vector_distance,
            'vector' as method
            FROM current_image_embeddings cie
            JOIN images i ON cie.image_id = i.image_id
            WHERE (cie.embedding <#> %s) < -0.1 -- ここでフィルタリング
            ORDER BY vector_distance
        """
        # "vector"を文字列として扱いたい場合、シングルクォートで囲む
    if search_method == "テキスト検索":
        query_embedding = json.dumps(compute_text_embeddings(query).tolist()[0])
        # json.dumps: PythonオブジェクトをJSON形式に変換
        # ex) [0.1, 0.2, 0.3] -> "[0.1, 0.2, 0.3]"
        # 理由: データベースにはJSON形式で保存されているから
        
    elif search_method == "画像検索":
        if isinstance(query, UploadedFile):
            query = Image.open(query)
        query_embedding = json.dumps(compute_image_embeddings(query).tolist()[0])
    else:
        raise ValueError("無効な検索方法です")
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(query_str, (query_embedding, query_embedding))
            rows = cur.fetchall()

    processed_results = [{
        "image_id": row["image_id"],
        "file_name": row["file_name"],
        "score": row["vector_distance"],
        "method": row["method"]
    } for row in rows]

    print(f"検索結果: {len(processed_results)}件") 
    return processed_results