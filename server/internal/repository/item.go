package repository

import (
	"needful/internal/entities"
)

type ItemRepository interface {
	GetAllItem() ([]entities.Item, error)
	GetItemByUserId(int) ([]entities.Item, error)
	GetItemByItemId(int) (*entities.Item, error)

	////////////////////////////////////////////////////////////////////

	GetItemDetailsByItemId(int) (*entities.Item, error)

	/////////////////////////////////////////////////////////////////

	GetAllItemOfCurrentUser(int) ([]entities.ItemsOfCurrentUserResponse, error)
	GetDonateItemsOfCurrentUser(int) ([]entities.DonateItemsOfCurrentUserResponse, error)
	GetReceiveItemsOfCurrentUser(int) ([]entities.ReceiveItemsOfCurrentUserResponse, error)

	PostAddItem(item *entities.Item) error

	DeleteItemByItemId(itemID int) error

	GetMarketPlace(int) ([]entities.MarketPlaceResponse, error)
	GetDonateMarketPlace(int) ([]entities.DonateMarketPlaceResponse, error)
	GetReceiveMarketPlace(int) ([]entities.ReceiveMarketPlaceResponse, error)

	PutAskByItemId(item *entities.Item) error
	PostAskMessage(message *entities.Message) error

	PutTransactionReady(item *entities.Item) error
	PutCompleteTransaction(item *entities.Item) error
}
