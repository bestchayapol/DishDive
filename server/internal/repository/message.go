package repository

import (
	"needful/internal/entities"
)

type MessageRepository interface {
	GetAllMessage() ([]entities.Message, error)
	GetMessageByUserId(int) ([]entities.Message, error)
	GetMessageByMsgId(int) (*entities.Message, error)

	GetMessagePageOfCurrentUser(int) ([]entities.MessagePageOfCurrentUserResponse, error)
	GetConversationOfCurrentUserByOtherID(int, int) ([]entities.ConversationOfCurrentUserByOtherIDResponse, error)
	PostMessage(message *entities.Message) error
}
