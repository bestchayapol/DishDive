package entities

type User struct {
	UserID    *uint `gorm:"column:user_id;primaryKey;autoIncrement" json:"user_id"`
	Username  *string `gorm:"column:user_name;size:100;uniqueIndex;not null" json:"username"`
	Password  *string `gorm:"column:password;size:100;not null" json:"password"`
	Email     *string `gorm:"column:email;size:100;uniqueIndex;not null" json:"email"`
	Firstname *string `gorm:"column:firstname;size:100;not null" json:"first_name"`
	Lastname  *string `gorm:"column:lastname;size:100;not null" json:"last_name"`
	PhoneNum  *string `gorm:"column:phone_num;size:15;not null" json:"phone_num"`
	UserPic   *string `gorm:"column:user_pic;size:255" json:"user_pic,omitempty"`
}

type Restaurant struct {
    RestaurantID uint      `gorm:"column:res_id;primaryKey;autoIncrement" json:"restaurant_id"`
    RestaurantName         string    `gorm:"column:res_name;size:255;not null" json:"name"`
	Cuisine		*string   `gorm:"column:res_cuisine;size:100;not null" json:"cuisine"`	
    Restriction *string   `gorm:"column:res_restriction;size:100" json:"restriction,omitempty"`
	MenuSize    *string   `gorm:"column:res_menu_size;size:100" json:"menu_size,omitempty"`
	UsableReview *uint     `gorm:"column:usable_rev" json:"usable,omitempty"`
	TotalReview	 *uint     `gorm:"column:total_rev" json:"total,omitempty"`
}

type Dish struct {
	DishID      *uint   `gorm:"column:dish_id;primaryKey;autoIncrement" json:"dish_id"`
	RestaurantID uint    `gorm:"column:res_id;not null;index" json:"restaurant_id"`
	DishName        *string `gorm:"column:dish_name;size:255;not null" json:"dish_name"`
	Cuisine		*string   `gorm:"column:dish_cuisine;size:100;not null" json:"cuisine"`
	Restriction *string   `gorm:"column:restriction;size:100" json:"restriction,omitempty"`
	PositiveScore *uint   `gorm:"column:positive_score" json:"positive_score,omitempty"`
	NegativeScore *uint   `gorm:"column:negative_score" json:"negative_score,omitempty"`
	TotalScore    *float64   `gorm:"column:total_score" json:"total_score,omitempty"`
}


