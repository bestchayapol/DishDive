package repository

import (
	"gorm.io/gorm"
	"needful/internal/entities"
)

type messageRepositoryDB struct {
	db *gorm.DB
}

func NewMessageRepositoryDB(db *gorm.DB) messageRepositoryDB {
	return messageRepositoryDB{db: db}
}

func (r messageRepositoryDB) GetAllMessage() ([]entities.Message, error) {
	messages := []entities.Message{}
	result := r.db.Find(&messages)
	if result.Error != nil {
		return nil, result.Error
	}
	return messages, nil
}

func (r messageRepositoryDB) GetMessageByUserId(userid int) ([]entities.Message, error) {
	messages := []entities.Message{}
	result := r.db.Where("sender_user_id = ? OR receiver_user_id = ?", userid, userid).Find(&messages)
	if result.Error != nil {
		return nil, result.Error
	}
	return messages, nil
}

func (r messageRepositoryDB) GetMessageByMsgId(messageid int) (*entities.Message, error) {
	messages := entities.Message{}
	result := r.db.Where("msg_id = ?", messageid).Find(&messages)
	if result.Error != nil {
		return nil, result.Error
	}
	return &messages, nil
}

func (r messageRepositoryDB) GetMessagePageOfCurrentUser(userid int) ([]entities.MessagePageOfCurrentUserResponse, error) {
	messages := []entities.MessagePageOfCurrentUserResponse{}

	subquery := r.db.Table("messages AS m").
		Select("MAX(m.msg_id) as msg_id").
		Where("m.sender_user_id = ? OR m.receiver_user_id = ?", userid, userid).
		Group("LEAST(m.sender_user_id, m.receiver_user_id), GREATEST(m.sender_user_id, m.receiver_user_id)")

	result := r.db.Table("messages AS m").
		Select(`
			m.msg_id,
			m.sender_user_id,
			m.receiver_user_id,
			m.msg_text,
			u.user_id,
			u.username,
			u.firstname,
			u.lastname,
			u.user_pic
		`).
		Joins("JOIN (?) AS sub ON sub.msg_id = m.msg_id", subquery).
		Joins("JOIN users AS u ON u.user_id = m.sender_user_id OR u.user_id = m.receiver_user_id").
		Where("(m.sender_user_id = ? OR m.receiver_user_id = ?) AND u.user_id != ?", userid, userid, userid).
		Group("m.msg_id, m.sender_user_id, m.receiver_user_id, m.msg_text, u.user_id, u.username, u.firstname, u.lastname, u.user_pic").
		Order("msg_id DESC").
		Scan(&messages)

	if result.Error != nil {
		return nil, result.Error
	}
	return messages, nil
}

func (r messageRepositoryDB) GetConversationOfCurrentUserByOtherID(currentUserID int, otherUserID int) ([]entities.ConversationOfCurrentUserByOtherIDResponse, error) {
	conversations := []entities.ConversationOfCurrentUserByOtherIDResponse{}

	// Assuming you have a GORM setup
	result := r.db.Table("messages").
		Select("messages.*, users.user_id, users.username, users.firstname, users.lastname, users.user_pic").
		Joins("left join users on users.user_id = messages.sender_user_id").
		Where("(messages.sender_user_id = ? AND messages.receiver_user_id = ?) OR (messages.sender_user_id = ? AND messages.receiver_user_id = ?)", currentUserID, otherUserID, otherUserID, currentUserID).
		Order("msg_id DESC").
		Scan(&conversations)

	if result.Error != nil {
		return nil, result.Error
	}
	return conversations, nil
}

func (r messageRepositoryDB) PostMessage(message *entities.Message) error {
	result := r.db.Create(message)
	if result.Error != nil {
		return result.Error
	}
	return nil
}
