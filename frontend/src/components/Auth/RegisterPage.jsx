import React, { useState } from 'react';

const RegisterPage = () => {
  const [tab, setTab] = useState('email');

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-4xl bg-white rounded-lg shadow-lg overflow-hidden flex">
        
        {/* Formulario de Registro */}
        <div className="w-1/2 p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Create Your Account</h2>
          <p className="text-gray-500 mb-6">Register with your email or mobile</p>

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
          <form className="space-y-4">
            {tab === 'email' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email address</label>
                  <input type="email" className="mt-1 w-full border px-3 py-2 rounded-md focus:ring-2 focus:ring-green-400" />
                </div>
              </>
            )}
            {tab === 'mobile' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Phone number</label>
                  <input type="tel" className="mt-1 w-full border px-3 py-2 rounded-md focus:ring-2 focus:ring-green-400" />
                </div>
              </>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <input type="password" className="mt-1 w-full border px-3 py-2 rounded-md focus:ring-2 focus:ring-green-400" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Referral ID</label>
              <input type="text" className="mt-1 w-full border px-3 py-2 rounded-md focus:ring-2 focus:ring-green-400" />
            </div>
            <button type="submit" className="w-full bg-green-500 text-white py-2 rounded-md hover:bg-green-600 transition">
              Create Account
            </button>
          </form>

          <p className="mt-4 text-sm text-gray-600">
            Already registered? <a href="/login" className="text-blue-600 hover:underline">Log IN</a>
          </p>
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

export default RegisterPage;
