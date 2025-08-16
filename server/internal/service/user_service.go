package service

import (
	"errors"
	"log"
	"strconv"

	"github.com/bestchayapol/DishDive/internal/dtos"
	"github.com/bestchayapol/DishDive/internal/entities"
	"github.com/bestchayapol/DishDive/internal/repository"
	"github.com/gofiber/fiber/v2"
	"github.com/golang-jwt/jwt/v4"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

type userService struct {
	userRepo  repository.UserRepository
	jwtSecret string
}

func NewUserService(userRepo repository.UserRepository, jwtSecret string) userService {
	return userService{
		userRepo:  userRepo,
		jwtSecret: jwtSecret,
	}
}

func (s userService) GetUsers() ([]entities.User, error) {
	users, err := s.userRepo.GetAllUser()
	if err != nil {
		log.Println(err)
		return nil, err
	}
	return users, nil
}

func (s userService) GetUserByUserId(userid int) (*entities.User, error) {
	user, err := s.userRepo.GetUserByUserId(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}
	if user.UserID == 0 && user.Username == nil && user.ImageLink == nil && user.PasswordHash == "" {
		return nil, fiber.NewError(fiber.StatusNotFound, "user data is not found")
	}
	return user, nil
}

func (s userService) GetUserByToken(userid int) (*entities.User, error) {
	user, err := s.userRepo.GetUserByToken(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}
	if user.UserID == 0 && user.Username == nil && user.ImageLink == nil && user.PasswordHash == "" {
		return nil, fiber.NewError(fiber.StatusNotFound, "user data is not found")
	}
	return user, nil
}

////////////////////////////////////////////////////////////////////////////////////

func (s userService) GetCurrentUser(userid int) (*entities.User, error) {
	user, err := s.userRepo.GetCurrentUser(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}
	return user, nil
}

func (s userService) GetProfileOfCurrentUserByUserId(userid int) (*entities.User, error) {
	user, err := s.userRepo.GetProfileOfCurrentUserByUserId(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}
	if user.UserID == 0 && user.Username == nil && user.ImageLink == nil && user.PasswordHash == "" {
		return nil, fiber.NewError(fiber.StatusNotFound, "user data is not found")
	}
	return user, nil
}

func (s userService) GetEditUserProfileByUserId(userid int) (*entities.User, error) {
	user, err := s.userRepo.GetEditUserProfileByUserId(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}
	if user.UserID == 0 && user.Username == nil && user.ImageLink == nil {
		return nil, fiber.NewError(fiber.StatusNotFound, "user data is not found")
	}
	return user, nil
}

func (s userService) PatchEditUserProfileByUserId(userid int, req dtos.EditUserProfileByUserIdRequest) (*entities.User, error) {
	user := &entities.User{
		UserID:      uint(userid),
		Username:   req.Username,
		ImageLink:   req.ImageLink,
	}

	err := s.userRepo.PatchEditUserProfileByUserId(user)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	return user, nil
}

func (s userService) Register(request dtos.RegisterRequest) (*dtos.UserResponse, error) {
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(request.PasswordHash), bcrypt.DefaultCost)
	if err != nil {
		return nil, err
	}

	user := entities.User{
		Username:     request.Username,
		ImageLink:    request.ImageLink,
		PasswordHash: string(hashedPassword),
	}

	err = s.userRepo.CreateUser(&user)
	if err != nil {
		return nil, err
	}

	return &dtos.UserResponse{
		UserID:    user.UserID,
		Username:  user.Username,
		ImageLink: user.ImageLink,
	}, nil

}

func (s userService) Login(request dtos.LoginRequest, jwtSecret string) (*dtos.LoginResponse, error) {
	username := *request.Username
	user, err := s.userRepo.GetUserByUsername(username)
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, fiber.NewError(fiber.StatusBadRequest, "invalid credentials")
		}
		return nil, err
	}

	// Compare password hash
	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(request.PasswordHash)); err != nil {
		return nil, fiber.NewError(fiber.StatusBadRequest, "invalid credentials")
	}

	// Generate JWT token
	claims := jwt.RegisteredClaims{
		Issuer: strconv.Itoa(int(user.UserID)),
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	jwtToken, err := token.SignedString([]byte(jwtSecret))
	if err != nil {
		return nil, err
	}

	return &dtos.LoginResponse{
		UserID:    user.UserID,
		Username:  user.Username,
		Token:     &jwtToken,
	}, nil
}
