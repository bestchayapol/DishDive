package service

import (
    "context"
    "fmt"
    "github.com/spf13/viper"
    "mime/multipart"

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

    fileURL := fmt.Sprintf("%s/%s/%s", viper.GetString("minio.publicURL"), bucketName, fileName)
    return &fileURL, err
}