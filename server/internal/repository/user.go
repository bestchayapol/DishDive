package repository

import "github.com/bestchayapol/DishDive/internal/entities"

type UserRepository interface {
	GetAllUser() ([]entities.User, error)
	GetUserByUserId(int) (*entities.User, error)
	GetUserByToken(int) (*entities.User, error)

	////////////////////////////////////////////////////////////////////

	GetCurrentUser(int) (*entities.User, error)

	GetProfileOfCurrentUserByUserId(int) (*entities.User, error)

	GetEditUserProfileByUserId(int) (*entities.User, error)
	PatchEditUserProfileByUserId(user *entities.User) error

	CreateUser(user *entities.User) error                      //Register
	GetUserByUsername(userName string) (*entities.User, error) //Login
}
