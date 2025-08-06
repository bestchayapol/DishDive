package service

import (
	"needful/internal/dtos"
	"needful/internal/entities"
)

type UserService interface {
	GetUsers() ([]entities.User, error)
	GetUserByUserId(int) (*entities.User, error)
	GetUserByToken(int) (*entities.User, error)

	////////////////////////////////////////////////////////////////////

	GetCurrentUser(int) (*entities.User, error)
	GetProfileOfCurrentUserByUserId(int) (*entities.User, error)

	GetEditUserProfileByUserId(int) (*entities.User, error)
	PatchEditUserProfileByUserId(int, dtos.EditUserProfileByUserIdRequest) (*entities.User, error)

	Register(request dtos.RegisterRequest) (*dtos.UserResponse, error)
	Login(request dtos.LoginRequest, jwtSecret string) (*dtos.LoginResponse, error)
}
