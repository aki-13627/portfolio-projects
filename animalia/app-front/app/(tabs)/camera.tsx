import { CreatePostModal } from '@/components/CreatePostModal';
import { useAuth } from '@/providers/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';
import {
  CameraView,
  CameraType,
  useCameraPermissions,
  FlashMode,
} from 'expo-camera';
import { useRouter } from 'expo-router';
import { useCallback, useRef, useState } from 'react';
import {
  Animated,
  Button,
  Dimensions,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  Linking,
} from 'react-native';

const { height } = Dimensions.get('window');
export type TaskType = 'eating' | 'sleeping' | 'playing';

export const taskTypeMap: Record<TaskType, string> = {
  eating: 'ご飯を食べているところを撮影しよう！',
  sleeping: '寝ているところを撮影しよう！',
  playing: '遊んでいるところを撮影しよう！',
};

export default function CameraScreen() {
  const router = useRouter();
  const [permission, requestPermission] = useCameraPermissions();
  const [facing, setFacing] = useState<CameraType>('back');
  const [flashMode, setFlashMode] = useState<FlashMode>('off');
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [showTaskMessage, setShowTaskMessage] = useState(false);
  const cameraRef = useRef<any>(null);
  const { user: currentUser } = useAuth();

  const slideAnim = useRef(new Animated.Value(height)).current;
  useFocusEffect(
    useCallback(() => {
      slideAnim.setValue(height);
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }).start();
    }, [slideAnim])
  );
  const handleClose = () => {
    Animated.timing(slideAnim, {
      toValue: height,
      duration: 100,
      useNativeDriver: true,
    }).start(() => {
      router.replace('/(tabs)/posts');
    });
  };

  const taskButtonColor = showTaskMessage ? 'green' : 'white';

  const dailyTaskDone = currentUser?.dailyTask.post ? true : false;

  if (!permission) return null;

  return (
    <Animated.View
      style={[styles.container, { transform: [{ translateY: slideAnim }] }]}
    >
      {!permission.granted ? (
        <View style={styles.permissionOverlay}>
          <Text style={styles.permissionText}>カメラの許可が必要です</Text>
          {permission.canAskAgain ? (
            <Button title="許可をリクエスト" onPress={requestPermission} />
          ) : (
            <Button title="設定を開く" onPress={() => Linking.openSettings()} />
          )}
        </View>
      ) : photoUri ? (
        <CreatePostModal
          photoUri={photoUri}
          onClose={() => setPhotoUri(null)}
          dailyTaskId={
            !dailyTaskDone && showTaskMessage
              ? currentUser?.dailyTask.id
              : undefined
          }
        />
      ) : (
        <CameraView
          ref={cameraRef}
          style={styles.camera}
          facing={facing}
          flash={flashMode}
        >
          {currentUser?.dailyTask && currentUser.dailyTask.post == null && (
            <TouchableOpacity
              style={[styles.taskButton, { backgroundColor: taskButtonColor }]}
              onPress={() => setShowTaskMessage(!showTaskMessage)}
            >
              <Text style={styles.taskButtonText}>Today’s Task 🐾</Text>
            </TouchableOpacity>
          )}
          {!dailyTaskDone && showTaskMessage && currentUser?.dailyTask && (
            <View style={styles.taskMessageContainer}>
              <Text style={styles.taskMessageText}>
                {taskTypeMap[currentUser.dailyTask.type as TaskType]}
              </Text>
            </View>
          )}
          <TouchableOpacity style={styles.closeButton} onPress={handleClose}>
            <Text style={styles.closeText}>×</Text>
          </TouchableOpacity>

          <View style={styles.bottomControls}>
            <TouchableOpacity
              style={styles.flashButton}
              onPress={() =>
                setFlashMode((prev) => (prev === 'off' ? 'on' : 'off'))
              }
            >
              <Ionicons
                name={flashMode === 'off' ? 'flash-off' : 'flash'}
                size={30}
                color={flashMode === 'off' ? '#888' : '#facc15'}
              />
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.shutterButton}
              onPress={async () => {
                if (cameraRef.current) {
                  const photo = await cameraRef.current.takePictureAsync();
                  setPhotoUri(photo.uri);
                }
              }}
            />

            <TouchableOpacity
              style={styles.flipButton}
              onPress={() =>
                setFacing((prev) => (prev === 'back' ? 'front' : 'back'))
              }
            >
              <Text style={styles.flipText}>↺</Text>
            </TouchableOpacity>
          </View>
        </CameraView>
      )}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  permissionOverlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.6)',
    padding: 16,
  },
  permissionText: {
    color: '#fff',
    fontSize: 18,
    textAlign: 'center',
    marginBottom: 20,
  },
  camera: { flex: 1 },
  bottomControls: {
    position: 'absolute',
    bottom: 40,
    width: '100%',
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  flashButton: {
    marginRight: 50,
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  flashText: {
    color: '#fff',
    fontSize: 16,
    textAlign: 'center',
  },
  shutterButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#fff',
    borderWidth: 4,
    borderColor: '#ccc',
  },
  flipButton: {
    marginLeft: 50,
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  flipText: {
    color: '#fff',
    fontSize: 24,
    textAlign: 'center',
  },
  closeButton: {
    position: 'absolute',
    top: 60,
    left: 20,
    width: 50,
    borderRadius: 12,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1,
  },
  closeText: {
    color: '#fff',
    fontSize: 24,
    textAlign: 'center',
  },
  taskButton: {
    position: 'absolute',
    top: 60,
    right: 20,
    backgroundColor: '#fff',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    zIndex: 3,
  },
  taskButtonText: {
    fontWeight: 'bold',
    fontSize: 14,
    color: '#333',
  },
  taskMessageContainer: {
    position: 'absolute',
    top: '40%',
    left: 0,
    right: 0,
    alignItems: 'center',
    zIndex: 5,
  },
  taskMessageText: {
    color: '#000',
    fontSize: 20,
    opacity: 0.4,
    fontWeight: 'bold',
    textAlign: 'center',
    paddingHorizontal: 20,
  },
});
