package service

import (
	"errors"
	"github.com/dgrijalva/jwt-go"
	"github.com/gofiber/fiber/v2"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
	"log"
	"needful/internal/dtos"
	"needful/internal/entities"
	"needful/internal/repository"
	"needful/internal/utils/v"
	"strconv"
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

	userResponses := []entities.User{}
	for _, user := range users {
		userResponse := entities.User{
			UserID:    user.UserID,
			Username:  user.Username,
			Password:  user.Password,
			Email:     user.Email,
			Firstname: user.Firstname,
			Lastname:  user.Lastname,
			PhoneNum:  user.PhoneNum,
			UserPic:   user.UserPic,
		}
		userResponses = append(userResponses, userResponse)
	}
	return userResponses, nil
}

func (s userService) GetUserByUserId(userid int) (*entities.User, error) {
	user, err := s.userRepo.GetUserByUserId(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	if user.UserID == nil &&
		user.Username == nil &&
		user.Password == nil &&
		user.Email == nil &&
		user.Firstname == nil &&
		user.Lastname == nil &&
		user.PhoneNum == nil &&
		user.UserPic == nil {
		return nil, fiber.NewError(fiber.StatusNotFound, "user data is not found")
	}

	userResponse := entities.User{
		UserID:    user.UserID,
		Username:  user.Username,
		Password:  user.Password,
		Email:     user.Email,
		Firstname: user.Firstname,
		Lastname:  user.Lastname,
		PhoneNum:  user.PhoneNum,
		UserPic:   user.UserPic,
	}
	return &userResponse, nil
}

func (s userService) GetUserByToken(userid int) (*entities.User, error) {
	user, err := s.userRepo.GetUserByToken(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	if user.UserID == nil &&
		user.Username == nil &&
		user.Password == nil &&
		user.Email == nil &&
		user.Firstname == nil &&
		user.Lastname == nil &&
		user.PhoneNum == nil &&
		user.UserPic == nil {
		return nil, fiber.NewError(fiber.StatusNotFound, "user data is not found")
	}

	userResponse := entities.User{
		UserID:    user.UserID,
		Username:  user.Username,
		Password:  user.Password,
		Email:     user.Email,
		Firstname: user.Firstname,
		Lastname:  user.Lastname,
		PhoneNum:  user.PhoneNum,
		UserPic:   user.UserPic,
	}
	return &userResponse, nil
}

////////////////////////////////////////////////////////////////////////////////////

func (s userService) GetCurrentUser(userid int) (*entities.User, error) {
	user, err := s.userRepo.GetCurrentUser(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	userResponse := entities.User{
		UserID:    user.UserID,
		Username:  user.Username,
		Password:  user.Password,
		Email:     user.Email,
		Firstname: user.Firstname,
		Lastname:  user.Lastname,
		PhoneNum:  user.PhoneNum,
		UserPic:   user.UserPic,
	}
	return &userResponse, nil
}

func (s userService) GetProfileOfCurrentUserByUserId(userid int) (*entities.User, error) {
	user, err := s.userRepo.GetProfileOfCurrentUserByUserId(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	if user.UserID == nil &&
		user.Username == nil &&
		user.Password == nil &&
		user.Email == nil &&
		user.Firstname == nil &&
		user.Lastname == nil &&
		user.PhoneNum == nil &&
		user.UserPic == nil {
		return nil, fiber.NewError(fiber.StatusNotFound, "user data is not found")
	}

	userResponse := entities.User{
		UserID:    user.UserID,
		Username:  user.Username,
		Password:  user.Password,
		Email:     user.Email,
		Firstname: user.Firstname,
		Lastname:  user.Lastname,
		PhoneNum:  user.PhoneNum,
		UserPic:   user.UserPic,
	}
	return &userResponse, nil
}

func (s userService) GetEditUserProfileByUserId(userid int) (*entities.User, error) {
	user, err := s.userRepo.GetEditUserProfileByUserId(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	if user.UserID == nil &&
		user.Username == nil &&
		user.Password == nil &&
		user.Email == nil &&
		user.Firstname == nil &&
		user.Lastname == nil &&
		user.PhoneNum == nil &&
		user.UserPic == nil {
		return nil, fiber.NewError(fiber.StatusNotFound, "user data is not found")
	}

	userResponse := entities.User{
		UserID:    user.UserID,
		Username:  user.Username,
		Email:     user.Email,
		Firstname: user.Firstname,
		Lastname:  user.Lastname,
		PhoneNum:  user.PhoneNum,
	}
	return &userResponse, nil
}

func (s userService) PatchEditUserProfileByUserId(userid int, req dtos.EditUserProfileByUserIdRequest) (*entities.User, error) {
	user := &entities.User{
		UserID:    v.UintPtr(userid),
		Username:  req.Username,
		Email:     req.Email,
		Firstname: req.Firstname,
		Lastname:  req.Lastname,
		PhoneNum:  req.PhoneNum,
	}

	err := s.userRepo.PatchEditUserProfileByUserId(user)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	return user, nil
}

func (s userService) Register(request dtos.RegisterRequest) (*dtos.UserResponse, error) {
	hashedPassword, err := bcrypt.GenerateFromPassword(v.ByteSlice(request.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, err
	}

	user := entities.User{
		Username:  request.Username,
		Password:  v.Ptr(string(hashedPassword)),
		Email:     request.Email,
		Firstname: request.Firstname,
		Lastname:  request.Lastname,
		PhoneNum:  request.PhoneNum,
		UserPic:   request.UserPic,
	}

	err = s.userRepo.CreateUser(&user)
	if err != nil {
		return nil, err
	}

	return &dtos.UserResponse{
		UserID:   user.UserID,
		Username: user.Username,
		UserPic:  user.UserPic,
	}, nil

}

func (s userService) Login(request dtos.LoginRequest, jwtSecret string) (*dtos.LoginResponse, error) {
	username := *request.Username

	user, err := s.userRepo.GetUserByUsername(username)
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, fiber.NewError(fiber.StatusBadRequest, "invalid username or password")
		}
		return nil, err
	}

	// Compare password
	if err := bcrypt.CompareHashAndPassword(v.ByteSlice(user.Password), []byte(*request.Password)); err != nil {
		return nil, fiber.NewError(fiber.StatusBadRequest, "invalid credentials")
	}

	// Generate JWT token
	claims := jwt.StandardClaims{
		Issuer: strconv.Itoa(int(*user.UserID)),
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	jwtToken, err := token.SignedString([]byte(jwtSecret))
	if err != nil {
		return nil, err
	}

	return &dtos.LoginResponse{
		UserID:   user.UserID,
		Username: user.Username,
		Token:    &jwtToken,
	}, nil
}
