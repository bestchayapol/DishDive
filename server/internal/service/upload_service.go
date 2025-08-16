package service

import (
	"context"
	"fmt"
	"mime/multipart"

	"github.com/minio/minio-go/v7"
)

type uploadService struct {
	client        *minio.Client
	bucket        string
	publicBaseURL *string
}

func NewUploadService(client *minio.Client, bucket string, publicBaseURL *string) UploadService {
	return &uploadService{client: client, bucket: bucket, publicBaseURL: publicBaseURL}
}

func (s *uploadService) UploadFile(file *multipart.FileHeader) (*string, error) {
	ctx := context.Background()
	buffer, err := file.Open()
	if err != nil {
		return nil, err
	}

	defer buffer.Close()

	fileName := file.Filename

	_, err = s.client.PutObject(ctx, s.bucket, fileName, buffer, file.Size, minio.PutObjectOptions{
		ContentType: "application/octet-stream",
	})
	if err != nil {
		return nil, err
	}

	// Build a public URL for the uploaded object
	var imageLink string
	if s.publicBaseURL != nil && *s.publicBaseURL != "" {
		imageLink = fmt.Sprintf("%s/%s/%s", *s.publicBaseURL, s.bucket, fileName)
	} else {
		// Fallback: relative path; frontends can prefix with API/static host if proxied
		imageLink = fmt.Sprintf("/%s/%s", s.bucket, fileName)
	}
	return &imageLink, err
}
