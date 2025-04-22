package usecase

import (
	"mime/multipart"

	"github.com/aki-13627/animalia/backend-go/internal/domain/repository"
)

type StorageUsecase struct {
	storageRepository repository.StorageRepository
}

func NewStorageUsecase(storageRepository repository.StorageRepository) *StorageUsecase {
	return &StorageUsecase{storageRepository: storageRepository}
}

func (u *StorageUsecase) UploadImage(file *multipart.FileHeader, directory string) (string, error) {
	return u.storageRepository.UploadImage(file, directory)
}

func (u *StorageUsecase) GetUrl(fileKey string) (string, error) {
	return u.storageRepository.GetUrl(fileKey)
}

func (u *StorageUsecase) DeleteImage(fileKey string) error {
	return u.storageRepository.DeleteImage(fileKey)
}
