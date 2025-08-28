package entities

type User struct {
    UserID    uint    `gorm:"column:user_id;primaryKey;autoIncrement" json:"user_id"`
    Username  *string  `gorm:"column:user_name;size:100;not null" json:"user_name"`
    ImageLink *string `gorm:"column:image_link;size:255" json:"image_link,omitempty"`
	PasswordHash string `gorm:"column:password_hash;size:255;not null" json:"password_hash"`
}

type Restaurant struct {
    ResID          uint    `gorm:"column:res_id;primaryKey;autoIncrement" json:"res_id"`
    ResName        string  `gorm:"column:res_name;size:255;not null" json:"res_name"`
    ResCuisine     *string `gorm:"column:res_cuisine;size:100" json:"res_cuisine,omitempty"`
    ResRestriction *string `gorm:"column:res_restriction;size:100" json:"res_restriction,omitempty"`
    MenuSize       int     `gorm:"column:menu_size;not null" json:"menu_size"`
    UsableRev      int     `gorm:"column:usable_rev;not null" json:"usable_rev"`
    TotalRev       int     `gorm:"column:total_rev;not null" json:"total_rev"`
}

type RestaurantLocation struct {
    RLID        uint    `gorm:"column:rl_id;primaryKey;autoIncrement" json:"rl_id"`
    ResID       uint    `gorm:"column:res_id;not null;index" json:"res_id"`
    LocationName string  `gorm:"column:location_name;size:255;not null" json:"location_name"`
    Address     string  `gorm:"column:address;size:255" json:"address,omitempty"`
    Latitude    float64 `gorm:"column:latitude" json:"latitude"`
    Longitude   float64 `gorm:"column:longitude" json:"longitude"`
}

type Dish struct {
    DishID        uint    `gorm:"column:dish_id;primaryKey;autoIncrement" json:"dish_id"`
    ResID         uint    `gorm:"column:res_id;not null;index" json:"res_id"`
    DishName      string  `gorm:"column:dish_name;size:255;not null" json:"dish_name"`
    Cuisine       *string `gorm:"column:cuisine;size:100" json:"cuisine,omitempty"`
    Restriction   *string `gorm:"column:restriction;size:100" json:"restriction,omitempty"`
    PositiveScore int     `gorm:"column:positive_score;not null" json:"positive_score"`
    NegativeScore int     `gorm:"column:negative_score;not null" json:"negative_score"`
    TotalScore    float64 `gorm:"column:total_score;not null" json:"total_score"`
}

type DishAlias struct {
    DAID    uint   `gorm:"column:da_id;primaryKey;autoIncrement" json:"da_id"`
    DishID  uint   `gorm:"column:dish_id;not null;index" json:"dish_id"`
    AltName string `gorm:"column:alt_name;size:255;not null" json:"alt_name"`
}

type Keyword struct {
    KeywordID uint   `gorm:"column:keyword_id;primaryKey;autoIncrement" json:"keyword_id"`
    Keyword   string `gorm:"column:keyword;size:100;not null" json:"keyword"`
    Category  string `gorm:"column:category;size:100" json:"category,omitempty"`
    Sentiment string `gorm:"column:sentiment;size:100;not null" json:"sentiment"`
}

type KeywordAlias struct {
    KAID      uint   `gorm:"column:ka_id;primaryKey;autoIncrement" json:"ka_id"`
    KeywordID uint   `gorm:"column:keyword_id;not null;index" json:"keyword_id"`
    AltWord   string `gorm:"column:alt_word;size:100;not null" json:"alt_word"`
}


type Favorite struct {
    UserID uint `gorm:"column:user_id;not null;index" json:"user_id"`
    DishID uint `gorm:"column:dish_id;not null;index" json:"dish_id"`
}


type DishKeyword struct {
    DishID    uint `gorm:"column:dish_id;not null;index" json:"dish_id"`
    KeywordID uint `gorm:"column:keyword_id;not null;index" json:"keyword_id"`
    Frequency uint `gorm:"column:frequency;not null" json:"frequency"`
}


type PreferenceBlacklist struct {
    UserID     uint    `gorm:"column:user_id;not null;index" json:"user_id"`
    KeywordID  uint    `gorm:"column:keyword_id;not null;index" json:"keyword_id"`
    Preference float64 `gorm:"column:preference" json:"preference,omitempty"`
    Blacklist  float64 `gorm:"column:blacklist" json:"blacklist,omitempty"`
}


type UserReview struct {
    UserRevID uint   `gorm:"column:user_rev_id;primaryKey;autoIncrement" json:"user_rev_id"`
    UserID    uint   `gorm:"column:user_id;not null;index" json:"user_id"`
    DishID    uint   `gorm:"column:dish_id;not null;index" json:"dish_id"`
    ResID     uint   `gorm:"column:res_id;not null;index" json:"res_id"`
    UserRev   string `gorm:"column:user_rev;type:text;not null" json:"user_rev"`
}

