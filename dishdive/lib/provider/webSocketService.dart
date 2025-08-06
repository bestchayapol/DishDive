import 'dart:async';
import 'dart:convert';
import 'package:dishdive/Components/integrate_model.dart';
import 'package:web_socket_channel/web_socket_channel.dart';


class WebSocketService {
  final WebSocketChannel _channel;
  final StreamController<List<MessageLog>> _messagesController = StreamController.broadcast();

  WebSocketService(String url) : _channel = WebSocketChannel.connect(Uri.parse(url)) {
    _channel.stream.listen((data) {
      final List<dynamic> jsonData = jsonDecode(data);
      final List<MessageLog> messages = jsonData.map((json) => MessageLog.fromJson(json)).toList();
      _messagesController.add(messages);
    });
  }

  Stream<List<MessageLog>> get messagesStream => _messagesController.stream;

  void dispose() {
    _channel.sink.close();
    _messagesController.close();
  }
}
