package service

import (
	"context"
	"fmt"
	"mime/multipart"

	"github.com/spf13/viper"

	"github.com/minio/minio-go/v7"
)

type uploadService struct {
	client *minio.Client
}

func NewUploadService(client *minio.Client) UploadService {
	return &uploadService{client: client}
}

func (s *uploadService) UploadFile(file *multipart.FileHeader) (*string, error) {
	ctx := context.Background()
	buffer, err := file.Open()
	if err != nil {
		return nil, err
	}

	defer buffer.Close()

	fileName := file.Filename

	bucketName := viper.GetString("minio.bucket")

	_, err = s.client.PutObject(ctx, bucketName, fileName, buffer, file.Size, minio.PutObjectOptions{
		ContentType: file.Header.Get("Content-Type"),
	})
	if err != nil {
		return nil, err
	}

	// Construct the public URL correctly
	// Use HTTP instead of HTTPS for local development with port
	fileURL := fmt.Sprintf("http://%s/%s/%s",
		fmt.Sprintf("%s:%d", viper.GetString("minio.host"), viper.GetInt("minio.port")),
		bucketName,
		fileName)
	return &fileURL, err
}
