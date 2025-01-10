'use client';

import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper 
} from '@mui/material';
import axios from 'axios';

interface Match {
  index: string;
  date_of_match: string;
  team: string;
  opponent: string;
  xg: number;
  xga: number;
  Result: number;
  location_of_match: string;
  rolling_xg: number;
  rolling_xga: number;
  rolling_xg_diff: number;
  rolling_xga_diff: number;
  form_rolling_5: number;
  form_rolling_10: number;
  opponent_form_rolling_3: number;
  opponent_form_rolling_6: number;
  Status: string;
}

export default function Home() {
  const [rawData, setRawData] = useState<Match[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);

  useEffect(() => {
    const fetchMatches = async () => {
      console.log('Starting API fetch...');
      try {
        const response = await axios.get('https://localhost:5001/matches', {
          headers: {
            'Content-Type': 'application/json',
          }
        });
        console.log('Raw API Response:', response.data);
        console.log('First match object:', response.data[0]);
        console.log('Types of first match:', {
        index: typeof response.data[0]?.index,
        Date: typeof response.data[0]?.Date,
        Team: typeof response.data[0]?.Team,
        xg: typeof response.data[0]?.xg,
        xga: typeof response.data[0]?.xga,
        });

        console.log('Raw API Response:', response.data);
        setMatches(response.data);
        
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
          Matches
        </Typography>

        {error && (
          <Typography color="error" sx={{ my: 2 }}>
            Error: {error}
          </Typography>
        )}

        <TableContainer component={Paper}>
          <Table sx={{ minWidth: 650 }} aria-label="matches table">
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Team</TableCell>
                <TableCell>Opponent</TableCell>
                <TableCell>xG</TableCell>
                <TableCell>xGA</TableCell>
                <TableCell>Result</TableCell>
                <TableCell>Location</TableCell>
                <TableCell>Rolling xG</TableCell>
                <TableCell>Rolling xGA</TableCell>
                <TableCell>Rolling xG Diff</TableCell>
                <TableCell>Rolling xGA Diff</TableCell>
                <TableCell>Form Rolling 5</TableCell>
                <TableCell>Form Rolling 10</TableCell>
                <TableCell>Opponent Form Rolling 3</TableCell>
                <TableCell>Opponent Form Rolling 6</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {matches.map((match, index) => (
                <TableRow key={`${match.index}-${index}`}>
                  <TableCell>{match.date_of_match}</TableCell>
                  <TableCell>{match.team}</TableCell>
                  <TableCell>{match.opponent}</TableCell>
                  <TableCell>{match.xg}</TableCell>
                  <TableCell>{match.xga}</TableCell>
                  <TableCell>{match.Result}</TableCell>
                  <TableCell>{match.location_of_match}</TableCell>
                  <TableCell>{match.rolling_xg}</TableCell>
                  <TableCell>{match.rolling_xga}</TableCell>
                  <TableCell>{match.rolling_xg_diff}</TableCell>
                  <TableCell>{match.rolling_xga_diff}</TableCell>
                  <TableCell>{match.form_rolling_5}</TableCell>
                  <TableCell>{match.form_rolling_10}</TableCell>
                  <TableCell>{match.opponent_form_rolling_3}</TableCell>
                  <TableCell>{match.opponent_form_rolling_6}</TableCell>
                  <TableCell>{match.Status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Container>
  );
}