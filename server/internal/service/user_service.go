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
	userRepo      repository.UserRepository
	recommendRepo repository.RecommendRepository
	jwtSecret     string
}

func NewUserService(userRepo repository.UserRepository, recommendRepo repository.RecommendRepository, jwtSecret string) userService {
	return userService{
		userRepo:      userRepo,
		recommendRepo: recommendRepo,
		jwtSecret:     jwtSecret,
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
		UserID:    uint(userid),
		Username:  req.Username,
		ImageLink: req.ImageLink,
	}

	err := s.userRepo.PatchEditUserProfileByUserId(user)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	// Fetch the updated user data from database to return current values
	updatedUser, err := s.userRepo.GetUserByUserId(userid)
	if err != nil {
		log.Println(err)
		return nil, err
	}

	return updatedUser, nil
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

	// Initialize user preferences if they don't exist (happens on every login)
	err = s.ensureUserPreferencesExist(user.UserID)
	if err != nil {
		log.Printf("Warning: Failed to ensure preferences exist for user %d: %v", user.UserID, err)
		// Don't fail login if preference initialization fails
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
		UserID:   user.UserID,
		Username: user.Username,
		Token:    &jwtToken,
	}, nil
}

// Ensure user has all required preference settings (called on every login)
func (s userService) ensureUserPreferencesExist(userID uint) error {
	// Check if user already has preference settings
	existingSettings, err := s.recommendRepo.GetUserSettings(userID)
	if err != nil {
		return err
	}

	// Create a map of existing settings for quick lookup
	existingMap := make(map[uint]bool)
	for _, setting := range existingSettings {
		existingMap[setting.KeywordID] = true
	}

	log.Printf("User %d has %d existing preference settings", userID, len(existingSettings))
	
	var newSettings []entities.PreferenceBlacklist
	
	// 1. Get ALL keywords to filter from
	allKeywords, err := s.recommendRepo.GetKeywordsByCategory([]string{"flavor", "cost", "system", "cuisine", "restriction"})
	if err != nil {
		return err
	}
	
	// 2. Define the specific static keywords we want to initialize
	staticFlavorKeywords := []string{"Sweet", "Salty", "Sour", "Spicy", "Oily"}
	staticCostKeywords := []string{"Cheap", "Moderate", "Expensive"}
	
	// 3. Process keywords and add missing ones
	for _, keyword := range allKeywords {
		shouldInitialize := false
		
		switch keyword.Category {
		case "flavor":
			// Only initialize the 5 specific flavor keywords
			for _, staticFlavor := range staticFlavorKeywords {
				if keyword.Keyword == staticFlavor {
					shouldInitialize = true
					break
				}
			}
		case "cost":
			// Only initialize the 3 specific cost keywords
			for _, staticCost := range staticCostKeywords {
				if keyword.Keyword == staticCost {
					shouldInitialize = true
					break
				}
			}
		case "system":
			// Initialize all system keywords (just sentiment)
			shouldInitialize = true
		case "cuisine", "restriction":
			// Initialize all cuisine and restriction keywords (dynamic categories)
			shouldInitialize = true
		}
		
		// Only add to newSettings if it should be initialized AND doesn't already exist
		if shouldInitialize && !existingMap[keyword.KeywordID] {
			newSettings = append(newSettings, entities.PreferenceBlacklist{
				UserID:     userID,
				KeywordID:  keyword.KeywordID,
				Preference: 0, // Default: no preference
				Blacklist:  0, // Default: not blacklisted
			})
		}
	}

	// 4. Only bulk insert if there are new settings to add
	if len(newSettings) > 0 {
		log.Printf("Initializing %d new preference settings for user %d", len(newSettings), userID)
		return s.recommendRepo.BulkUpdateUserSettings(userID, newSettings)
	} else {
		log.Printf("User %d already has all required preference settings", userID)
		return nil
	}
}
