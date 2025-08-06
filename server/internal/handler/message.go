package handler

import (
	"errors"
	"github.com/gofiber/fiber/v2"
	"needful/internal/dtos"
	"needful/internal/service"
	"needful/internal/utils"
	"strconv"
	"strings"
)

type messageHandler struct {
	messageSer service.MessageService
	jwtSecret  string
	uploadSer  service.UploadService
}

func NewMessageHandler(messageSer service.MessageService, jwtSecret string) messageHandler {
	return messageHandler{messageSer: messageSer, jwtSecret: jwtSecret}
}

func (h *messageHandler) GetMessages(c *fiber.Ctx) error {
	messagesResponse := make([]dtos.MessageDataResponse, 0)

	messages, err := h.messageSer.GetMessages()
	if err != nil {
		return err
	}

	for _, message := range messages {
		messagesResponse = append(messagesResponse, dtos.MessageDataResponse{
			MsgID:          message.MsgID,
			SenderUserID:   message.SenderUserID,
			ReceiverUserID: message.ReceiverUserID,
			MsgText:        message.MsgText,
		})
	}
	return c.JSON(messagesResponse)
}

func (h *messageHandler) GetMessageByUserId(c *fiber.Ctx) error {

	userIDReceive, err := strconv.Atoi(c.Params("UserID"))

	messagesResponse := make([]dtos.MessageDataByUserIdResponse, 0)
	message, err := h.messageSer.GetMessageByUserId(userIDReceive)
	if err != nil {
		return err
	}

	for _, message := range message {
		messagesResponse = append(messagesResponse, dtos.MessageDataByUserIdResponse{
			MsgID:          message.MsgID,
			SenderUserID:   message.SenderUserID,
			ReceiverUserID: message.ReceiverUserID,
			MsgText:        message.MsgText,
		})
	}
	return c.JSON(messagesResponse)
}

func (h *messageHandler) GetMessageByMsgId(c *fiber.Ctx) error {
	messageIDReceive, err := strconv.Atoi(c.Params("MsgID"))

	message, err := h.messageSer.GetMessageByMsgId(messageIDReceive)
	if err != nil {
		return err
	}

	messageResponse := dtos.MessageDataByMsgIdResponse{
		MsgID:          message.MsgID,
		SenderUserID:   message.SenderUserID,
		ReceiverUserID: message.ReceiverUserID,
		MsgText:        message.MsgText,
	}

	return c.JSON(messageResponse)
}

func (h *messageHandler) GetMessagePageOfCurrentUser(c *fiber.Ctx) error {
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

	messages, err := h.messageSer.GetMessagePageOfCurrentUser(userIDExtract)
	if err != nil {
		return err
	}

	messagesResponse := make([]dtos.MessagePageOfCurrentUserResponse, 0)
	for _, message := range messages {
		messagesResponse = append(messagesResponse, dtos.MessagePageOfCurrentUserResponse{
			UserID:         message.UserID,
			Username:       message.Username,
			Firstname:      message.Firstname,
			Lastname:       message.Lastname,
			UserPic:        message.UserPic,
			MsgID:          message.MsgID,
			SenderUserID:   message.SenderUserID,
			ReceiverUserID: message.ReceiverUserID,
			MsgText:        message.MsgText,
		})
	}
	return c.JSON(messagesResponse)
}

func (h *messageHandler) GetConversationOfCurrentUserByOtherID(c *fiber.Ctx) error {
	otherIDReceive, err := strconv.Atoi(c.Params("OtherID"))
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

	messages, err := h.messageSer.GetConversationOfCurrentUserByOtherID(userIDExtract, otherIDReceive)
	if err != nil {
		return err
	}

	messagesResponse := make([]dtos.ConversationOfCurrentUserByOtherIDResponse, 0)
	for _, message := range messages {
		messagesResponse = append(messagesResponse, dtos.ConversationOfCurrentUserByOtherIDResponse{
			UserID:         message.UserID,
			Username:       message.Username,
			Firstname:      message.Firstname,
			Lastname:       message.Lastname,
			UserPic:        message.UserPic,
			MsgID:          message.MsgID,
			SenderUserID:   message.SenderUserID,
			ReceiverUserID: message.ReceiverUserID,
			MsgText:        message.MsgText,
		})
	}
	return c.JSON(messagesResponse)
}

func (h *messageHandler) PostMessage(c *fiber.Ctx) error {
	receiverIDReceive, err := strconv.Atoi(c.Params("ReceiverID"))
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

	var request dtos.MessageRequest
	if err := c.BodyParser(&request); err != nil {
		return err
	}

	message, err := h.messageSer.PostMessage(userIDExtract, receiverIDReceive, request)
	if err != nil {
		return err
	}

	messageResponse := dtos.MessageRequest{
		SenderUserID:   message.SenderUserID,
		ReceiverUserID: message.ReceiverUserID,
		MsgText:        message.MsgText,
	}

	return c.JSON(messageResponse)
}
