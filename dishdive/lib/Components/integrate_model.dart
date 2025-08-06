class Itemlist {
 final int itemlistId;         // Renamed from item_id for consistency
 final int userId;
 final String itemname;
 final String description;     // Added to match the JSON
 final String itemPic;
 final String offerType;       // Renamed for consistency, was offer_type
 final int? askedByUserId;      // Renamed for consistency, was asked_by_user_id
 final bool? alreadyGave;       // Renamed for consistency, was already_gave
 final String? username;
 final String? userPic;         // Added to match the JSON
 final String? usernameAskedByUserId; // Renamed for consistency

  Itemlist({
    required this.itemlistId,
    required this.userId,
    required this.itemname,
    required this.description, // Now required since it's in JSON
    required this.itemPic,
    required this.offerType,
    required this.askedByUserId,
    required this.alreadyGave,
    required this.username,
    required this.userPic, 
    required this.usernameAskedByUserId,
  });

  factory Itemlist.fromJson(Map<String, dynamic> json) {
    return Itemlist(
      itemlistId: json['item_id'],
      userId: json['user_id'],
      itemname: json['itemname'],
      description: json['description'], 
      itemPic: json['item_pic'],
      offerType: json['offer_type'],
      askedByUserId: json['asked_by_user_id'],
      alreadyGave: json['already_gave'],
      username: json['username'],
      userPic: json['user_pic'],
      usernameAskedByUserId: json['username_asked_by_user_id'],
    );
  }
}


class WishlistItem {
  final int id;
  final String product;
  final String grantBy;
  final int price;
  final String linkUrl;
  final String itemPic;
  // ... other properties

  WishlistItem({
    required this.id,
    required this.product,
    required this.grantBy,
    required this.price,
    required this.linkUrl,
    required this.itemPic,
  });
}

class WishItem {
  final int wishlistId;
  final int userId;
  final String itemname;
  final int price;
  final String linkurl;
  final String itemPic;
  final bool? alreadyBought;
  final int? grantedByUserId;
  final String usernameOfWishlist;
  final String? picOfWishlistUser;

  WishItem(
      {required this.wishlistId,
      required this.userId,
      required this.itemname,
      required this.price,
      required this.linkurl,
      required this.itemPic,
      this.alreadyBought,
      this.grantedByUserId,
      required this.usernameOfWishlist,
      this.picOfWishlistUser});

  factory WishItem.fromJson(Map<String, dynamic> json) {
    return WishItem(
      wishlistId: json['wishlist_id'],
      userId: json['user_id'],
      itemname: json['itemname'],
      price: json['price'],
      linkurl: json['link_url'],
      itemPic: json['item_pic'],
      alreadyBought: json['already_bought'],
      grantedByUserId: json['granted_by_user_id'],
      usernameOfWishlist: json['username_of_wishlist'],
      picOfWishlistUser: json['user_pic_of_wishlist'],
    );
  }
}


class MessageLog {
  final int userid;
  final String firstname;
  final String lastname;
  final String username;
  final String user_pic;
  final int msgId;
  final int senderuserId;
  final int receiveuserId;
  final String latestMessage;

  MessageLog({
    required this.userid,
    required this.firstname,
    required this.lastname,
    required this.msgId,
    required this.senderuserId,
    required this.receiveuserId,
    required this.username,
    required this.latestMessage,
    required this.user_pic,
  });

  factory MessageLog.fromJson(Map<String, dynamic> json) {
    return MessageLog(
      userid: json['user_id'],
      firstname: json['firstname'],
      lastname: json['lastname'],
      msgId: json['msg_id'],
      senderuserId: json['sender_user_id'],
      receiveuserId: json['receiver_user_id'],
      username: json['username'],
      latestMessage: json['msg_text'],
      user_pic: json['user_pic'],
    );
  }
}

class ChatMessages {
  final int userid;
  final String firstname;
  final String lastname;
  final String username;
  final String user_pic;
  final int msgId;
  final int senderuserId;
  final int receiveuserId;
  final String msgText;

  ChatMessages({
    required this.userid,
    required this.firstname,
    required this.lastname,
    required this.msgId,
    required this.senderuserId,
    required this.receiveuserId,
    required this.username,
    required this.msgText,
    required this.user_pic,
  });

  factory ChatMessages.fromJson(Map<String, dynamic> json) {
    return ChatMessages(
      userid: json['user_id'],
      firstname: json['firstname'],
      lastname: json['lastname'],
      msgId: json['msg_id'],
      senderuserId: json['sender_user_id'],
      receiveuserId: json['receiver_user_id'],
      username: json['username'],
      msgText: json['msg_text'],
      user_pic: json['user_pic'],
    );
  }
}