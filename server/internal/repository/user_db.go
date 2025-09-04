package repository

import (
	"fmt"

	"github.com/bestchayapol/DishDive/internal/entities"

	"gorm.io/gorm"
)

type userRepositoryDB struct {
	db *gorm.DB
}

func NewUserRepositoryDB(db *gorm.DB) userRepositoryDB {
	return userRepositoryDB{db: db}
}

func (r userRepositoryDB) GetAllUser() ([]entities.User, error) {
	users := []entities.User{}
	result := r.db.Find(&users)
	if result.Error != nil {
		return nil, result.Error
	}
	return users, nil
}

func (r userRepositoryDB) GetUserByUserId(userid int) (*entities.User, error) {
	users := entities.User{}
	result := r.db.Where("user_id = ?", userid).Find(&users)
	if result.Error != nil {
		return nil, result.Error
	}
	return &users, nil
}

func (r userRepositoryDB) GetUserByToken(userid int) (*entities.User, error) {
	users := entities.User{}
	result := r.db.Where("user_id = ?", userid).Find(&users)
	if result.Error != nil {
		return nil, result.Error
	}
	return &users, nil
}

/////////////////////////////////////////////////////////////////////////////////////////////

func (r userRepositoryDB) GetCurrentUser(userid int) (*entities.User, error) {
	users := entities.User{}
	result := r.db.Where("user_id = ?", userid).Find(&users)
	if result.Error != nil {
		return nil, result.Error
	}
	return &users, nil
}

func (r userRepositoryDB) GetProfileOfCurrentUserByUserId(userid int) (*entities.User, error) {
	users := entities.User{}
	result := r.db.Where("user_id = ?", userid).Find(&users)
	if result.Error != nil {
		return nil, result.Error
	}
	return &users, nil
}

func (r userRepositoryDB) GetEditUserProfileByUserId(userid int) (*entities.User, error) {
	users := entities.User{}
	result := r.db.Where("user_id = ?", userid).Find(&users)
	if result.Error != nil {
		return nil, result.Error
	}
	return &users, nil
}

func (r userRepositoryDB) PatchEditUserProfileByUserId(user *entities.User) error {
	// Use Select to only update non-zero fields or use a map for selective updates
	updates := make(map[string]interface{})

	if user.Username != nil {
		updates["user_name"] = *user.Username
		fmt.Printf("DEBUG: Updating username to: %s\n", *user.Username)
	}
	if user.ImageLink != nil {
		updates["image_link"] = *user.ImageLink
		fmt.Printf("DEBUG: Updating image_link to: %s\n", *user.ImageLink)
	}

	// Only proceed if there are fields to update
	if len(updates) == 0 {
		fmt.Printf("DEBUG: No updates needed\n")
		return nil // No updates needed
	}

	fmt.Printf("DEBUG: Executing update for user_id: %d with updates: %+v\n", user.UserID, updates)
	result := r.db.Model(&entities.User{}).Where("user_id = ?", user.UserID).Updates(updates)
	if result.Error != nil {
		fmt.Printf("DEBUG: Update error: %v\n", result.Error)
		return result.Error
	}

	fmt.Printf("DEBUG: Update successful, rows affected: %d\n", result.RowsAffected)
	return nil
}

func (r userRepositoryDB) CreateUser(user *entities.User) error {
	result := r.db.Create(user)
	if result.Error != nil {
		return result.Error
	}
	return nil
}

func (r userRepositoryDB) GetUserByUsername(username string) (*entities.User, error) {
	var user entities.User
	result := r.db.Where("user_name = ?", username).First(&user)
	if result.Error != nil {
		return nil, result.Error
	}
	return &user, nil
}
