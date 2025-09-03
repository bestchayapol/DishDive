import 'package:flutter/material.dart';
import 'package:dishdive/Pages/Home/FirstHomePage.dart';
import 'package:dishdive/pages/Auth/LoR.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:dishdive/welcome.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:geolocator/geolocator.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (context) => TokenProvider()),
        ChangeNotifierProvider(create: (context) => WelcomeProvider()),
      ],
      child: const MainApp(),
    ),
  );
}

class WelcomeProvider with ChangeNotifier {
  bool _isWelcomeShown = false;

  bool get isWelcomeShown => _isWelcomeShown;

  Future<void> checkWelcomeStatus() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    _isWelcomeShown = prefs.getBool('isWelcomeShown') ?? false;
    notifyListeners();
  }

  Future<void> setWelcomeShown() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isWelcomeShown', true);
    _isWelcomeShown = true;
    notifyListeners();
  }
}

class MainApp extends StatefulWidget {
  const MainApp({super.key});

  @override
  _MainAppState createState() => _MainAppState();
}

class _MainAppState extends State<MainApp> {
  Position? _currentPosition;

  @override
  void initState() {
    super.initState();
    Provider.of<WelcomeProvider>(context, listen: false).checkWelcomeStatus();
    Provider.of<TokenProvider>(context, listen: false).loadToken();
  }

  Future<void> _getLocation() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) return;

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) return;
    }
    if (permission == LocationPermission.deniedForever) return;

    Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high);
    setState(() {
      _currentPosition = position;
    });

    // Send location to backend
    // Example using Dio:
    // Dio dio = Dio();
    // await dio.post('http://your-backend-url/location', data: {
    //   'latitude': position.latitude,
    //   'longitude': position.longitude,
    // });
  }


  @override
  Widget build(BuildContext context) {
    final tokenProvider = Provider.of<TokenProvider>(context);
    final welcomeProvider = Provider.of<WelcomeProvider>(context);

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(fontFamily: 'InriaSans'),
      home:
          // home: Home(),
          !welcomeProvider.isWelcomeShown
          ? Welcome(
              onFinished: () {
                welcomeProvider.setWelcomeShown();
              },
            )
          : !tokenProvider.isAuthenticated
          ? const LoginOrRegister()
          : const FirstHomePage(),
    );
  }
}
