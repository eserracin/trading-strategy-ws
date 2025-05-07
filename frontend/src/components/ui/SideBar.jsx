import React from 'react';
import { FaHome, FaBell, FaThLarge } from 'react-icons/fa';
import {useAuth} from '../../context/authContext';
import { useNavigate } from 'react-router-dom';
import AvatarMenu from './AvatarMenu';

const Sidebar = ({ user }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login'); // Redirigir a la página de inicio de sesión
  };


  return (
    <div className="h-screen w-20 bg-white border-r border-gray-200 flex flex-col justify-between items-center py-4 shadow-md">
      
      {/* Top Icons */}
      <div className="space-y-6">
        <div className="text-xl text-gray-700 hover:text-green-500 cursor-pointer">
          <FaThLarge />
        </div>
        <div className="text-xl text-gray-700 hover:text-green-500 cursor-pointer">
          <FaHome />
        </div>
        <div className="text-xl text-gray-700 hover:text-green-500 cursor-pointer">
          <FaBell />
        </div>
      </div>

      {/* Avatar abajo */}
      <div className="mb-2">
        <AvatarMenu user={user} onLogout={handleLogout} />
      </div>
    </div>
  );
};

export default Sidebar;
