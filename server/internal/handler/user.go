package handler

import (
	"errors"
	"fmt"
	"strconv"
	"strings"

	"github.com/bestchayapol/DishDive/internal/dtos"
	"github.com/bestchayapol/DishDive/internal/service"
	"github.com/bestchayapol/DishDive/internal/utils"
	"github.com/gofiber/fiber/v2"
)

type userHandler struct {
	userSer   service.UserService
	jwtSecret string
	uploadSer service.UploadService
}

func NewUserHandler(userSer service.UserService, jwtSecret string, uploadSer service.UploadService) userHandler {
	return userHandler{userSer: userSer, jwtSecret: jwtSecret, uploadSer: uploadSer}
}

func (h *userHandler) GetUsers(c *fiber.Ctx) error {
	usersResponse := make([]dtos.UserDataResponse, 0)

	users, err := h.userSer.GetUsers()
	if err != nil {
		return err
	}

	for _, user := range users {
		usersResponse = append(usersResponse, dtos.UserDataResponse{
			UserID:   user.UserID,
			Username: user.Username,

			ImageLink:    user.ImageLink,
			PasswordHash: user.PasswordHash,
		})
	}
	return c.JSON(usersResponse)
}

func (h *userHandler) GetUserByUserId(c *fiber.Ctx) error {
	userIDReceive, err := strconv.Atoi(c.Params("UserID"))

	user, err := h.userSer.GetUserByUserId(userIDReceive)
	if err != nil {
		return err
	}

	userResponse := dtos.UserByUserIdDataResponse{
		UserID:       user.UserID,
		Username:     user.Username,
		ImageLink:    user.ImageLink,
		PasswordHash: user.PasswordHash,
	}

	return c.JSON(userResponse)
}

func (h *userHandler) GetUserByToken(c *fiber.Ctx) error {
	// Extract the token from the request headers
	token := c.Get("Authorization")

	// Check if the token is empty
	if token == "" {
		return errors.New("token is missing")
	}

	// Extract the user ID from the token
	userIDExtract, err := utils.ExtractUserIDFromToken(strings.Replace(token, "Bearer ", "", 1), h.jwtSecret)
	if err != nil {
		return err
	}

	user, err := h.userSer.GetUserByToken(userIDExtract)
	if err != nil {
		return err
	}

	userResponse := dtos.UserByTokenDataResponse{
		UserID:       user.UserID,
		Username:     user.Username,
		ImageLink:    user.ImageLink,
		PasswordHash: user.PasswordHash,
	}

	return c.JSON(userResponse)
}

/////////////////////////////////////////////////////////////////////////

func (h *userHandler) GetCurrentUser(c *fiber.Ctx) error {
	// Extract the token from the request headers
	token := c.Get("Authorization")

	// Check if the token is empty
	if token == "" {
		return errors.New("token is missing")
	}

	// Extract the user ID from the token
	userIDExtract, err := utils.ExtractUserIDFromToken(strings.Replace(token, "Bearer ", "", 1), h.jwtSecret)
	if err != nil {
		return err
	}

	user, err := h.userSer.GetCurrentUser(userIDExtract)
	if err != nil {
		return err
	}

	userResponse := dtos.CurrentUserResponse{
		UserID:       user.UserID,
		Username:     user.Username,
		ImageLink:    user.ImageLink,
		PasswordHash: user.PasswordHash,
	}

	return c.JSON(userResponse)
}

func (h *userHandler) GetProfileOfCurrentUserByUserId(c *fiber.Ctx) error {
	userIDReceive, err := strconv.Atoi(c.Params("UserID"))

	user, err := h.userSer.GetProfileOfCurrentUserByUserId(userIDReceive)
	if err != nil {
		return err
	}

	userResponse := dtos.ProfileOfCurrentUserByUserIdResponse{
		UserID:    user.UserID,
		Username:  user.Username,
		ImageLink: user.ImageLink,
	}

	return c.JSON(userResponse)
}

func (h *userHandler) GetEditUserProfileByUserId(c *fiber.Ctx) error {
	userIDReceive, err := strconv.Atoi(c.Params("UserID"))

	user, err := h.userSer.GetEditUserProfileByUserId(userIDReceive)
	if err != nil {
		return err
	}

	userResponse := dtos.EditUserProfileByUserIdResponse{
		UserID:    user.UserID,
		Username:  user.Username,
		ImageLink: user.ImageLink,
	}

	return c.JSON(userResponse)
}

func (h *userHandler) PatchEditUserProfileByUserId(c *fiber.Ctx) error {
	userIDReceive, err := strconv.Atoi(c.Params("UserID"))
	if err != nil {
		return fiber.NewError(fiber.StatusBadRequest, "Invalid user ID")
	}

	// Handle both form data (with potential file upload) and JSON
	username := c.FormValue("user_name")

	fmt.Printf("DEBUG: Received username: '%s'\n", username)

	var imageURL *string

	// Check if a file is uploaded
	file, err := c.FormFile("file")
	if err == nil && file != nil {
		fmt.Printf("DEBUG: File uploaded: %s\n", file.Filename)
		// File uploaded, use upload service
		uploadedURL, uploadErr := h.uploadSer.UploadFile(file)
		if uploadErr != nil {
			return fiber.NewError(fiber.StatusInternalServerError, "Failed to upload image")
		}
		imageURL = uploadedURL
		fmt.Printf("DEBUG: Image URL generated: %s\n", *imageURL)
	} else {
		fmt.Printf("DEBUG: No file uploaded\n")
	}

	// Allow username-only updates (remove the validation that blocks empty imageURL)
	// Create request object - only include fields that are provided
	req := dtos.EditUserProfileByUserIdRequest{}
	if username != "" {
		req.Username = &username
		fmt.Printf("DEBUG: Setting username in request\n")
	}
	if imageURL != nil {
		req.ImageLink = imageURL
		fmt.Printf("DEBUG: Setting image URL in request\n")
	}

	fmt.Printf("DEBUG: About to call service layer\n")

	user, err := h.userSer.PatchEditUserProfileByUserId(userIDReceive, req)
	if err != nil {
		return err
	}

	userResponse := dtos.EditUserProfileByUserIdResponse{
		UserID:    user.UserID,
		Username:  user.Username,
		ImageLink: user.ImageLink,
	}

	return c.JSON(userResponse)
}

func (h *userHandler) Register(c *fiber.Ctx) error {
	// Parse multipart form data directly instead of JSON
	username := c.FormValue("user_name")
	password := c.FormValue("password_hash")

	// Validate required fields
	if username == "" {
		return fiber.NewError(fiber.StatusBadRequest, "Username is required")
	}
	if password == "" {
		return fiber.NewError(fiber.StatusBadRequest, "Password is required")
	}

	// Check if a file is uploaded
	file, err := c.FormFile("file")
	if err != nil {
		return fiber.NewError(fiber.StatusBadRequest, "Profile picture is required")
	}

	// Call upload service to upload the file
	fileURL, err := h.uploadSer.UploadFile(file)
	if err != nil {
		return fiber.NewError(fiber.StatusInternalServerError, "Failed to upload profile picture")
	}

	// Create the register request
	request := dtos.RegisterRequest{
		Username:     &username,
		ImageLink:    fileURL,
		PasswordHash: password,
	}

	response, err := h.userSer.Register(request)
	if err != nil {
		return fiber.NewError(fiber.StatusInternalServerError, err.Error())
	}

	return c.Status(fiber.StatusCreated).JSON(response)
}

func (h *userHandler) Login(c *fiber.Ctx) error {
	var request dtos.LoginRequest
	if err := c.BodyParser(&request); err != nil {
		return fiber.NewError(fiber.StatusBadRequest, err.Error())
	}

	if request.Username == nil || request.PasswordHash == "" {
		return fiber.NewError(fiber.StatusBadRequest, "Username and Password are required")
	}

	response, err := h.userSer.Login(request, h.jwtSecret)
	if err != nil {
		return fiber.NewError(fiber.StatusUnauthorized, err.Error())
	}

	return c.JSON(response)
}
