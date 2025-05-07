import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext'; // Importa el contexto de autenticación
import { useNavigate } from 'react-router-dom';
import { loginUser } from '../../services/api'; // Importa la función de inicio de sesión desde el servicio API

const LoginPage = () => {
  const [tab, setTab] = useState('email');
  const [emailOrPhone, setEmailOrPhone] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth(); // Obtiene la función de inicio de sesión del contexto
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await loginUser(emailOrPhone, password);
      const { access_token } = response;
      login(access_token); // Llama a la función de inicio de sesión del contexto
      navigate('/'); // Redirige al usuario a la página principal
    } catch (error) {
      console.error('Error al iniciar sesión:', error);
    }
  }


  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-4xl bg-white rounded-lg shadow-lg overflow-hidden flex">
        
        {/* Formulario de Login */}
        <div className="w-1/2 p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-1">Account Login</h2>
          <p className="text-gray-500 mb-6">Welcome back! Log In with your Email, Phone number or QR code</p>

          {/* Tabs */}
          <div className="flex space-x-2 mb-4">
            <button
              onClick={() => setTab('email')}
              className={`px-4 py-2 rounded ${tab === 'email' ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-600'}`}
            >
              Email
            </button>
            <button
              onClick={() => setTab('mobile')}
              className={`px-4 py-2 rounded ${tab === 'mobile' ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-600'}`}
            >
              Mobile
            </button>
          </div>

          {/* Formulario */}
          <form className="space-y-4" onSubmit={handleLogin}>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                {tab === 'email' ? 'Email address' : 'Phone number'}
              </label>
              <input
                type={tab === 'email' ? 'email' : 'tel'}
                value={emailOrPhone}
                onChange={(e) => setEmailOrPhone(e.target.value)}
                className="mt-1 w-full border px-3 py-2 rounded-md focus:ring-2 focus:ring-green-400"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)} 
                className="mt-1 w-full border px-3 py-2 rounded-md focus:ring-2 focus:ring-green-400"
                required
              />
            </div>

            <button type="submit" className="w-full bg-green-500 text-white py-2 rounded-md hover:bg-green-600 transition">
              Log in
            </button>
          </form>

          <div className="flex justify-between mt-4 text-sm">
            <a href="/forgot-password" className="text-green-500 hover:underline">Forgot Password?</a>
            <a href="/register" className="text-green-500 hover:underline">Register Now</a>
          </div>
        </div>

        {/* QR Code */}
        <div className="w-1/2 bg-gray-50 flex flex-col justify-center items-center p-8">
          <img src="/qrcode-placeholder.png" alt="QR Code" className="w-40 h-40 mb-4" />
          <p className="text-gray-700 text-center">Log in with QR code</p>
          <p className="text-gray-500 text-center text-sm">
            Scan this code with the <a href="#" className="text-green-600 underline">Cryptoon mobile app</a><br />to log in instantly.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
