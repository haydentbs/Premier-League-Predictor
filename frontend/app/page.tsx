'use client';

import React, { useState, useEffect } from 'react';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Container, Typography, Box, Alert } from '@mui/material';
import axios from 'axios';
import { Match, ApiResponse } from '../types/types';

export default function Home() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMatches = async () => {
      console.log('Fetching matches from API...');
      try {
        const response = await axios.get<ApiResponse<Match[]>>('http://localhost:5001/api/matches', {
          headers: {
            'Content-Type': 'application/json',
          },
          timeout: 5000, // 5 second timeout
          withCredentials: true
        });
        
        console.log('API Response:', response.data);
        
        if (response.data && response.data.data) {
          console.log(`Received ${response.data.data.length} matches`);
          setMatches(response.data.data);
        } else {
          throw new Error('Invalid response format');
        }
      } catch (error: any) {
        console.error('Error details:', error);
        if (error.code === 'ERR_NETWORK') {
          setError('Cannot connect to the server. Please ensure the backend is running.');
        } else {
          setError(
            error.response 
              ? `Server error: ${error.response.data?.message || error.response.statusText}`
              : error.message || 'Failed to load matches'
          );
        }
      } finally {
        setLoading(false);
      }
    };

    fetchMatches();
  }, []);

  const columns: GridColDef[] = [
    { 
      field: 'match_date', 
      headerName: 'Date', 
      width: 130,
      valueFormatter: (params) => new Date(params.value).toLocaleDateString() 
    },
    { 
      field: 'home_team', 
      headerName: 'Home Team', 
      width: 150,
      renderCell: (params) => (
        <Box sx={{ fontWeight: 'bold' }}>
          {params.value}
        </Box>
      )
    },
    { 
      field: 'away_team', 
      headerName: 'Away Team', 
      width: 150 
    },
    { 
      field: 'score', 
      headerName: 'Score', 
      width: 120,
      renderCell: (params) => (
        <Box>
          {params.row.home_score ?? '-'} - {params.row.away_score ?? '-'}
        </Box>
      )
    },
    { 
      field: 'xg', 
      headerName: 'Expected Goals', 
      width: 150,
      renderCell: (params) => (
        <Box>
          {params.row.home_xg?.toFixed(2) ?? '-'} - {params.row.away_xg?.toFixed(2) ?? '-'}
        </Box>
      )
    },
    { 
      field: 'form', 
      headerName: 'Form (5/10)', 
      width: 150,
      renderCell: (params) => (
        <Box>
          {params.row.form_5?.toFixed(2) ?? '-'} / {params.row.form_10?.toFixed(2) ?? '-'}
        </Box>
      )
    },
    { 
      field: 'status', 
      headerName: 'Status', 
      width: 120,
      renderCell: (params) => (
        <Box sx={{ 
          bgcolor: params.value === 'yes' ? 'success.light' : 'info.light',
          px: 2,
          py: 0.5,
          borderRadius: 1
        }}>
          {params.value === 'yes' ? 'Finished' : 'Scheduled'}
        </Box>
      )
    }
  ];

  return (
    <Container maxWidth="lg">
      <Box sx={{ height: '100vh', width: '100%', p: 2 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Premier League Matches
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <DataGrid
          rows={matches}
          columns={columns}
          getRowId={(row) => row.match_id}
          initialState={{
            pagination: { paginationModel: { pageSize: 10 } },
            sorting: {
              sortModel: [{ field: 'match_date', sort: 'desc' }],
            },
          }}
          pageSizeOptions={[10, 25, 50]}
          autoHeight
          loading={loading}
          sx={{
            boxShadow: 2,
            border: 2,
            borderColor: 'primary.light',
            '& .MuiDataGrid-cell:hover': {
              color: 'primary.main',
            },
          }}
        />
      </Box>
    </Container>
  );
}