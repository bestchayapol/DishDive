package service

import (
	"needful/internal/dtos"
	"needful/internal/entities"
)

type MessageService interface {
	GetMessages() ([]entities.Message, error)
	GetMessageByUserId(int) ([]entities.Message, error)
	GetMessageByMsgId(int) (*entities.Message, error)

	GetMessagePageOfCurrentUser(int) ([]entities.MessagePageOfCurrentUserResponse, error)
	GetConversationOfCurrentUserByOtherID(int, int) ([]entities.ConversationOfCurrentUserByOtherIDResponse, error)
	PostMessage(int, int, dtos.MessageRequest) (*entities.Message, error)
}
