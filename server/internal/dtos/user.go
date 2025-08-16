package dtos

type UserDataResponse struct {
	UserID       uint    `json:"user_id"`
	Username     *string `json:"username"`
	ImageLink    *string `json:"image_link,omitempty"`
	PasswordHash string  `json:"password_hash"`
}

type UserByUserIdDataResponse struct {
	UserID       uint    `json:"user_id"`
	Username     *string `json:"username"`
	ImageLink    *string `json:"image_link,omitempty"`
	PasswordHash string  `json:"password_hash"`
}

type UserByTokenDataResponse struct {
	UserID       uint    `json:"user_id"`
	Username     *string `json:"username"`
	ImageLink    *string `json:"image_link,omitempty"`
	PasswordHash string  `json:"password_hash"`
}

//////////////////////////////////////////////////////////////////////////////

type CurrentUserResponse struct {
	UserID       uint    `json:"user_id"`
	Username     *string `json:"username"`
	ImageLink    *string `json:"image_link,omitempty"`
	PasswordHash string  `json:"password_hash"`
}

type ProfileOfCurrentUserByUserIdResponse struct {
	UserID    uint    `json:"user_id"`
	Username  *string `json:"username"`
	ImageLink *string `json:"image_link,omitempty"`
}

type EditUserProfileByUserIdResponse struct {
	UserID    uint    `json:"user_id"`
	Username  *string `json:"username"`
	ImageLink *string `json:"image_link,omitempty"`
}

type EditUserProfileByUserIdRequest struct {
	Username *string `json:"username"`
	ImageLink *string `json:"image_link,omitempty"`
}

type RegisterRequest struct {
	Username     *string  `json:"user_name"`
	ImageLink    *string `json:"image_link,omitempty"`
	PasswordHash string  `json:"password_hash"`
}

type LoginRequest struct {
	Username     *string `json:"user_name"`
	PasswordHash string `json:"password_hash"`
}

type UserResponse struct {
	UserID    uint    `json:"user_id"`
	Username  *string  `json:"user_name"`
	ImageLink *string `json:"image_link,omitempty"`
	Token     *string `json:"token,omitempty"`
}

type LoginResponse struct {
	UserID   uint    `json:"user_id"`
	Username *string  `json:"user_name"`
	Token    *string `json:"token,omitempty"`
}
