// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";  // Import Firebase Auth
import { getAnalytics } from "firebase/analytics";
import { getStorage } from 'firebase/storage';  // Ensure this is correct

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDbNBpXESyEZyRKYMFpmsPuizXKN-pnev8",
  authDomain: "g-drive-one.firebaseapp.com",
  projectId: "g-drive-one",
  storageBucket: "g-drive-one.appspot.com",
  messagingSenderId: "1009062829610",
  appId: "1:1009062829610:web:4b7fd99adb57184e9c2d53",
  measurementId: "G-NMLPFPVY71"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Analytics
const analytics = getAnalytics(app);

// Initialize Firebase Authentication and export it
const auth = getAuth(app);

export { auth };
export const storage = getStorage(app);