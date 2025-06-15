import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import FormInput from '../components/FormInput'; // Asegúrate de que exista
import { z } from 'zod';
import type { Finca } from '../types'; // Importación tipo-solo

const fincaSchema = z.object({
  name: z.string().min(1, 'Nombre es requerido'),
  location: z.string().min(1, 'Ubicación es requerida'),
});

export default function Fincas({ token }: { token: string }) {
  // Hooks de estado
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [fincas, setFincas] = useState<Finca[]>([]);
  const [message, setMessage] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  // Lógica derivada
  const filteredFincas = fincas.filter((finca: Finca) =>
    finca.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    finca.location.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Handlers
  const fetchFincas = useCallback(async () => {
    try {
      const response = await fetch('/api/fincas', { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error(`Error HTTP: ${response.status} ${response.statusText}`);
      const data: Finca[] = await response.json();
      setFincas(data);
    } catch (error) {
      console.error('Error al cargar fincas:', error);
      setMessage('Error al cargar fincas');
      setTimeout(() => setMessage(''), 3000);
    }
  }, [token]);

  useEffect(() => {
    fetchFincas();
  }, [fetchFincas]);

  const handleCreateFinca = async () => {
    const parseResult = fincaSchema.safeParse({ name, location });
    if (!parseResult.success) {
      setMessage(parseResult.error.errors[0].message);
      setTimeout(() => setMessage(''), 3000);
      return;
    }
    try {
      const response = await fetch('/api/fincas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(parseResult.data),
      });
      const data = await response.json();
      setMessage(data.message);
      setName(''); setLocation('');
      fetchFincas();
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Error al crear finca:', error);
      setMessage('Error al crear finca');
      setTimeout(() => setMessage(''), 3000);
    }
  };

  const handleEditFinca = (id: number) => {
    const finca = fincas.find((f: Finca) => f.id === id);
    if (finca) {
      setName(finca.name); setLocation(finca.location); setEditingId(id);
    }
  };

  const handleUpdateFinca = async () => {
    if (editingId) {
      const parseResult = fincaSchema.safeParse({ name, location });
      if (!parseResult.success) {
        setMessage(parseResult.error.errors[0].message);
        setTimeout(() => setMessage(''), 3000);
        return;
      }
      try {
        const response = await fetch(`/api/fincas/${editingId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify(parseResult.data),
        });
        const data = await response.json();
        setMessage(data.message);
        setName(''); setLocation(''); setEditingId(null);
        fetchFincas();
        setTimeout(() => setMessage(''), 3000);
      } catch (error) {
        console.error('Error al actualizar finca:', error);
        setMessage('Error al actualizar finca');
        setTimeout(() => setMessage(''), 3000);
      }
    }
  };

  const handleDeleteFinca = async (id: number) => {
    if (window.confirm('¿Seguro que quieres eliminar esta finca?')) {
      try {
        const response = await fetch(`/api/fincas/${id}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) throw new Error(`Error HTTP: ${response.status} ${response.statusText}`);
        fetchFincas();
        setMessage('Finca eliminada con éxito.');
        setTimeout(() => setMessage(''), 3000);
      } catch (error) {
        console.error('Error al eliminar finca:', error);
        setMessage('Error al eliminar finca');
        setTimeout(() => setMessage(''), 3000);
      }
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  // Renderizado
  return (
    <div className="min-h-screen bg-gray-100 p-4 sm:p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Gestión de Fincas</h1>
        <button onClick={handleLogout} className="mb-4 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition">
          Cerrar Sesión
        </button>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Buscar finca por nombre o ubicación..."
          className="w-full p-2 mb-4 border rounded"
        />
        <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">Crear/Editar Finca</h2>
          <FormInput label="Nombre" type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Nombre de la finca" />
          <FormInput label="Ubicación" type="text" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Ubicación" />
          <button onClick={editingId ? handleUpdateFinca : handleCreateFinca} className="w-full bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 mt-4 transition">
            {editingId ? 'Actualizar Finca' : 'Crear Finca'}
          </button>
          {message && <p className={`mt-4 text-center ${message.includes('Error') ? 'text-red-600' : 'text-green-600'}`} key={Date.now()}>{message}</p>}
          {editingId && <button onClick={() => { setName(''); setLocation(''); setEditingId(null); }} className="mt-2 text-red-500 underline">Cancelar Edición</button>}
        </div>
        <div className="mt-6 bg-white p-4 sm:p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">Lista de Fincas</h2>
          {filteredFincas.length === 0 ? (
            <p className="text-gray-500">No hay fincas registradas o que coincidan con la búsqueda.</p>
          ) : (
            <ul className="divide-y divide-gray-200">
              {filteredFincas.map((finca: Finca) => (
                <li key={finca.id} className="py-2 text-gray-700 flex flex-col sm:flex-row justify-between items-center">
                  <span className="mb-2 sm:mb-0"><strong>{finca.name}</strong> - {finca.location}</span>
                  <div className="flex flex-col sm:flex-row">
                    <button onClick={() => handleEditFinca(finca.id)} className="bg-yellow-500 text-white px-2 py-1 rounded mr-2 hover:bg-yellow-600 transition mb-2 sm:mb-0">Editar</button>
                    <button onClick={() => handleDeleteFinca(finca.id)} className="bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600 transition">Eliminar</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}