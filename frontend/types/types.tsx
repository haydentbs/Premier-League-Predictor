export interface Match {
    match_id: number;
    match_date: string;
    home_team: string;
    away_team: string;
    home_score: number | null;
    away_score: number | null;
    home_xg: number | null;
    away_xg: number | null;
    status: string;
    rolling_xg: number | null;
    rolling_xga: number | null;
    form_5: number | null;
    form_10: number | null;
    season?: string;
}

export interface ApiResponse<T> {
    message: string;
    data: T;
}