import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, CheckCircle, AlertTriangle } from 'lucide-react';
import { createMonitor } from '../lib/api';

const NewMonitorModal = ({ isOpen, onClose }) => {
  const [formData, setFormData] = useState({
    term: '',
    frequency: 'daily',
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.term) {
      setMessage('Please enter a keyword to monitor');
      setMessageType('error');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      await createMonitor({
        term: formData.term,
        frequency: formData.frequency,
      });

      setMessage(`Now monitoring attacks related to "${formData.term}" (${formData.frequency}).`);
      setMessageType('success');

      setTimeout(() => {
        onClose();
        window.location.reload();
      }, 2000);
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to create monitor. Please try again.';
      setMessage(errorMessage);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px] bg-gray-800 border-gray-700 text-white">
        <DialogHeader>
          <DialogTitle>Monitor a New Term</DialogTitle>
          <DialogDescription>
            Enter a keyword or product name to begin threat monitoring.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="term" className="text-gray-300">
              Keyword/Product Name *
            </Label>
            <Input
              id="term"
              name="term"
              placeholder="e.g., ATM fraud, POS malware, NCR"
              value={formData.term}
              onChange={handleInputChange}
              className="bg-gray-900 border-gray-600 text-white placeholder-gray-500 focus:border-cyan-400"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="frequency" className="text-gray-300">
              Monitoring Frequency
            </Label>
            <Select
              value={formData.frequency}
              onValueChange={(value) => setFormData({ ...formData, frequency: value })}
            >
              <SelectTrigger className="w-full bg-gray-900 border-gray-600 text-white">
                <SelectValue placeholder="Select frequency" />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700 text-white">
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {message && (
            <Alert className={messageType === 'success' ? 'border-green-500 bg-green-900/20' : 'border-red-500 bg-red-900/20'}>
              {messageType === 'success' ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <AlertTriangle className="h-4 w-4" />
              )}
              <AlertDescription className={messageType === 'success' ? 'text-green-300' : 'text-red-300'}>
                {message}
              </AlertDescription>
            </Alert>
          )}
          <DialogFooter>
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white font-semibold"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  <span>Monitoring...</span>
                </>
              ) : (
                'Monitor'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default NewMonitorModal;
