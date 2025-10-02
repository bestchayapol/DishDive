import 'package:flutter/foundation.dart';

class LocationProvider extends ChangeNotifier {
  double? _lat;
  double? _lng;

  double? get latitude => _lat;
  double? get longitude => _lng;
  bool get hasLocation => _lat != null && _lng != null;

  void setLocation(double lat, double lng) {
    _lat = lat;
    _lng = lng;
    notifyListeners();
  }
}
