export type TeamRouteLike={id:string;name:string};
export type GameRouteLike={id:string;season:number;awayName:string;homeName:string;neutral:boolean};

export const slugify=(value:string)=>value.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/&/g,' and ').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
export const teamSlug=(team:TeamRouteLike)=>slugify(team.name);
export const teamPath=(team:TeamRouteLike)=>`/teams/${teamSlug(team)}/`;
export const teamSeasonPath=(team:TeamRouteLike,season:number)=>`${teamPath(team)}${season}/`;
export const teamWeekPath=(team:TeamRouteLike,season:number,week:number)=>`${teamSeasonPath(team,season)}${snapshotSlug(week)}/`;
export const snapshotSlug=(week:number)=>week>=30?`postseason-${week-30}`:`week-${week}`;
export const rankingsPath=(season:number,latestSeason:number,week=99)=>week===99?(season===latestSeason?'/':`/rankings/${season}/`):`/rankings/${season}/${snapshotSlug(week)}/`;
export const gameSlug=(game:GameRouteLike)=>`${slugify(game.awayName)}-${game.neutral?'vs':'at'}-${slugify(game.homeName)}-${game.id}`;
export const gamePath=(game:GameRouteLike)=>`/games/${game.season}/${gameSlug(game)}/`;
