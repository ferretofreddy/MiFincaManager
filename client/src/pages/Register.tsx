import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import FormInput from '../components/FormInput';
import { z } from 'zod';

const registerSchema = z.object({
  username: z.string().min(3, 'Usuario debe tener al menos 3 caracteres'),
  password: z.string().min(6, 'Contraseña debe tener al menos 6 caracteres'),
});

export default function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const handleRegister = async () => {
    try {
      const result = registerSchema.parse({ username, password });
      const response = await fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(result),
      });
      const data = await response.json();
      if (data.message === 'Usuario creado') {
        navigate('/login');
      } else {
        setMessage(data.error || 'Error desconocido');
      }
    } catch (error) {
      if (error instanceof z.ZodError) {
        setMessage(error.errors[0].message);
      } else {
        setMessage('Error en la conexión');
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-6 rounded shadow-md w-96">
        <h1 className="text-2xl font-bold mb-4">Registrarse</h1>
        <FormInput label="Usuario" type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Usuario" />
        <FormInput label="Contraseña" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Contraseña" />
        <button onClick={handleRegister} className="w-full bg-green-500 text-white p-2 rounded hover:bg-green-600">
          Registrarse
        </button>
        {message && <p className="mt-4 text-center">{message}</p>}
        <p className="mt-4 text-center">
          ¿Ya tienes cuenta? <a href="/login" className="text-blue-500">Inicia Sesión</a>
        </p>
      </div>
    </div>
  );
}