package service

import (
	"needful/internal/dtos"
	"needful/internal/entities"
)

type ItemService interface {
	GetItems() ([]entities.Item, error)
	GetItemByUserId(int) ([]entities.Item, error)
	GetItemByItemId(int) (*entities.Item, error)

	///////////////////////////////////////////////////////////

	GetItemDetailsByItemId(int) (*entities.Item, error)

	///////////////////////////////////////////////////////////

	GetItemsOfCurrentUser(userid int) ([]entities.ItemsOfCurrentUserResponse, error)
	GetDonateItemsOfCurrentUser(userid int) ([]entities.DonateItemsOfCurrentUserResponse, error)
	GetReceiveItemsOfCurrentUser(userid int) ([]entities.ReceiveItemsOfCurrentUserResponse, error)

	PostAddItem(int, dtos.AddItemRequest) (*entities.Item, error)

	DeleteItemByItemId(itemID int) error

	GetMarketPlace(userid int) ([]entities.MarketPlaceResponse, error)
	GetDonateMarketPlace(userid int) ([]entities.DonateMarketPlaceResponse, error)
	GetReceiveMarketPlace(userid int) ([]entities.ReceiveMarketPlaceResponse, error)

	//PutAskByItemId(int, int) (*entities.Item, error)

	PutAskByItemIdAndPostAskMessage(int, int) (*entities.Item, error)

	PutTransactionReady(int, int) (*entities.Item, error)
	PutCompleteTransaction(int, int) (*entities.Item, error)
}
