'use client';

import React, { useState, useEffect } from 'react';
import { Container, Typography, Box } from '@mui/material';
import axios from 'axios';

export default function Home() {
  const [rawData, setRawData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMatches = async () => {
      console.log('Starting API fetch...');
      try {
        const response = await axios.get('http://localhost:5001/matches', {
          headers: {
            'Content-Type': 'application/json',
          }
        });
        
        console.log('Raw API Response:', response.data);
        setRawData(response.data);
        
      } catch (error) {
        console.error('Detailed error:', error);
        setError('Failed to load matches');
      }
    };

    fetchMatches();
  }, []);

  return (
    <Container>
      <Box sx={{ p: 2 }}>
        <Typography variant="h4" gutterBottom>
          Raw API Data
        </Typography>

        {error && (
          <Typography color="error" sx={{ my: 2 }}>
            Error: {error}
          </Typography>
        )}

        <Box sx={{ 
          backgroundColor: '#1e1e1e', 
          padding: '20px', 
          borderRadius: '4px',
          overflow: 'auto',
          maxHeight: '80vh'
        }}>
          <pre style={{ 
            margin: 0,
            color: '#d4d4d4',
            fontFamily: 'monospace',
            fontSize: '14px',
            lineHeight: '1.5'
          }}>
            {JSON.stringify(rawData, null, 2)}
          </pre>
        </Box>
      </Box>
    </Container>
  );
}