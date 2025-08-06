package repository

import (
	"needful/internal/entities"
	"needful/internal/utils/v"

	"gorm.io/gorm"
)

type itemRepositoryDB struct {
	db *gorm.DB
}

func NewItemRepositoryDB(db *gorm.DB) itemRepositoryDB {
	return itemRepositoryDB{db: db}
}

func (r itemRepositoryDB) GetAllItem() ([]entities.Item, error) {
	items := []entities.Item{}
	result := r.db.Find(&items)
	if result.Error != nil {
		return nil, result.Error
	}
	return items, nil
}

func (r itemRepositoryDB) GetItemByUserId(userid int) ([]entities.Item, error) {
	items := []entities.Item{}
	result := r.db.Where("user_id = ?", userid).Find(&items)
	if result.Error != nil {
		return nil, result.Error
	}
	return items, nil
}

func (r itemRepositoryDB) GetItemByItemId(itemid int) (*entities.Item, error) {
	items := entities.Item{}
	result := r.db.Where("item_id = ?", itemid).Find(&items)
	if result.Error != nil {
		return nil, result.Error
	}
	return &items, nil
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////

func (r itemRepositoryDB) GetItemDetailsByItemId(itemid int) (*entities.Item, error) {
	items := entities.Item{}
	result := r.db.Where("item_id = ?", itemid).Find(&items)
	if result.Error != nil {
		return nil, result.Error
	}
	return &items, nil
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////

//func (r itemRepositoryDB) GetAllItemOfCurrentUser(userid int) ([]dtos.ItemsOfCurrentUserResponse, error) {
//	items := []dtos.ItemsOfCurrentUserResponse{}
//	result := r.db.
//		Table("items").
//		Select(`
//			items.*,
//			users.username,
//			users.user_pic,
//			(SELECT u.username FROM users u WHERE u.user_id = items.asked_by_user_id) AS username_asked_by_user_id
//		`).
//		Joins("JOIN users ON items.user_id = users.user_id").
//		Where("users.user_id = ?", userid).
//		Find(&items)
//	if result.Error != nil {
//		return nil, result.Error
//	}
//	return items, nil
//}

func (r itemRepositoryDB) GetAllItemOfCurrentUser(userid int) ([]entities.ItemsOfCurrentUserResponse, error) {
	var items []struct {
		entities.ItemsOfCurrentUserResponse
		UsernameOfAskedByUserID string
	}
	result := r.db.
		Table("items").
		Select(`
            items.*,
            users.username,
            users.user_pic,
            (SELECT username FROM users WHERE user_id = items.asked_by_user_id) AS username_of_asked_by_user_id
        `).
		Joins("JOIN users ON items.user_id = users.user_id").
		Where("users.user_id = ? OR items.asked_by_user_id = ?", userid, userid).
		Find(&items)
	if result.Error != nil {
		return nil, result.Error
	}
	// Merge the nested field into the main struct
	for i, item := range items {
		items[i].ItemsOfCurrentUserResponse.UsernameOfAskedByUserID = v.Ptr(item.UsernameOfAskedByUserID)
	}
	// Convert to the desired response type
	var itemsResponse []entities.ItemsOfCurrentUserResponse
	for _, item := range items {
		itemsResponse = append(itemsResponse, item.ItemsOfCurrentUserResponse)
	}
	return itemsResponse, nil
}

func (r itemRepositoryDB) GetDonateItemsOfCurrentUser(userid int) ([]entities.DonateItemsOfCurrentUserResponse, error) {
	var items []struct {
		entities.DonateItemsOfCurrentUserResponse
		UsernameOfAskedByUserID string
	}
	result := r.db.
		Table("items").
		Select(`
            items.*,
            users.username,
            users.user_pic,
            (SELECT username FROM users WHERE user_id = items.asked_by_user_id) AS username_of_asked_by_user_id
        `).
		Joins("JOIN users ON items.user_id = users.user_id").
		Where("users.user_id = ?", userid).
		Where("offer_type = ?", "Donate").
		Or("items.asked_by_user_id = ? AND offer_type = ?", userid, "Receive").
		Find(&items)
	if result.Error != nil {
		return nil, result.Error
	}
	// Merge the nested field into the main struct
	for i, item := range items {
		items[i].DonateItemsOfCurrentUserResponse.UsernameOfAskedByUserID = v.Ptr(item.UsernameOfAskedByUserID)
	}
	// Convert to the desired response type
	var itemsResponse []entities.DonateItemsOfCurrentUserResponse
	for _, item := range items {
		itemsResponse = append(itemsResponse, item.DonateItemsOfCurrentUserResponse)
	}
	return itemsResponse, nil
}

func (r itemRepositoryDB) GetReceiveItemsOfCurrentUser(userid int) ([]entities.ReceiveItemsOfCurrentUserResponse, error) {
	var items []struct {
		entities.ReceiveItemsOfCurrentUserResponse
		UsernameOfAskedByUserID string
	}
	result := r.db.
		Table("items").
		Select(`
            items.*,
            users.username,
            users.user_pic,
            (SELECT username FROM users WHERE user_id = items.asked_by_user_id) AS username_of_asked_by_user_id
        `).
		Joins("JOIN users ON items.user_id = users.user_id").
		Where("users.user_id = ?", userid).
		Where("offer_type = ?", "Receive").
		Or("items.asked_by_user_id = ? AND offer_type = ?", userid, "Donate").
		Find(&items)
	if result.Error != nil {
		return nil, result.Error
	}
	// Merge the nested field into the main struct
	for i, item := range items {
		items[i].ReceiveItemsOfCurrentUserResponse.UsernameOfAskedByUserID = v.Ptr(item.UsernameOfAskedByUserID)
	}
	// Convert to the desired response type
	var itemsResponse []entities.ReceiveItemsOfCurrentUserResponse
	for _, item := range items {
		itemsResponse = append(itemsResponse, item.ReceiveItemsOfCurrentUserResponse)
	}
	return itemsResponse, nil
}

func (r itemRepositoryDB) PostAddItem(item *entities.Item) error {
	result := r.db.Create(item)
	if result.Error != nil {
		return result.Error
	}
	return nil
}

func (r itemRepositoryDB) DeleteItemByItemId(itemid int) error {
	items := entities.Item{}
	result := r.db.Where("item_id = ?", itemid).Unscoped().Delete(&items)
	if result.Error != nil {
		return result.Error
	}
	return nil
}

func (r itemRepositoryDB) GetMarketPlace(userid int) ([]entities.MarketPlaceResponse, error) {
	items := []entities.MarketPlaceResponse{}
	result := r.db.
		Table("items").
		Select(`
			items.*,
			users.username,
			users.user_pic
		`).
		Joins("JOIN users ON items.user_id = users.user_id").
		Where("users.user_id != ?", userid).
		Where("items.already_gave IS NULL").
		Where("items.asked_by_user_id IS NULL").
		Find(&items)
	if result.Error != nil {
		return nil, result.Error
	}
	return items, nil
}

func (r itemRepositoryDB) GetDonateMarketPlace(userid int) ([]entities.DonateMarketPlaceResponse, error) {
	items := []entities.DonateMarketPlaceResponse{}
	result := r.db.
		Table("items").
		Select(`
			items.*,
			users.username,
			users.user_pic
		`).
		Joins("JOIN users ON items.user_id = users.user_id").
		Where("users.user_id != ?", userid).
		Where("items.already_gave IS NULL").
		Where("items.asked_by_user_id IS NULL").
		Where("offer_type = ?", "Donate").
		Find(&items)
	if result.Error != nil {
		return nil, result.Error
	}
	return items, nil
}

func (r itemRepositoryDB) GetReceiveMarketPlace(userid int) ([]entities.ReceiveMarketPlaceResponse, error) {
	items := []entities.ReceiveMarketPlaceResponse{}
	result := r.db.
		Table("items").
		Select(`
			items.*,
			users.username,
			users.user_pic
		`).
		Joins("JOIN users ON items.user_id = users.user_id").
		Where("users.user_id != ?", userid).
		Where("items.already_gave IS NULL").
		Where("items.asked_by_user_id IS NULL").
		Where("offer_type = ?", "Receive").
		Find(&items)
	if result.Error != nil {
		return nil, result.Error
	}
	return items, nil
}

func (r itemRepositoryDB) PutAskByItemId(item *entities.Item) error {
	result := r.db.Save(item)
	if result.Error != nil {
		return result.Error
	}

	return nil
}

func (r itemRepositoryDB) PostAskMessage(message *entities.Message) error {
	result := r.db.Create(message)
	if result.Error != nil {
		return result.Error
	}
	return nil
}

func (r itemRepositoryDB) PutTransactionReady(item *entities.Item) error {
	result := r.db.Save(item)
	if result.Error != nil {
		return result.Error
	}

	return nil
}

func (r itemRepositoryDB) PutCompleteTransaction(item *entities.Item) error {
	result := r.db.Save(item)
	if result.Error != nil {
		return result.Error
	}

	return nil
}
