export type TeamRouteLike={id:string;name:string};
export type GameRouteLike={id:string;season:number;awayName:string;homeName:string;neutral:boolean};

export const slugify=(value:string)=>value.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/&/g,' and ').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
export const teamSlug=(team:TeamRouteLike)=>slugify(team.name);
export const teamPath=(team:TeamRouteLike)=>`/teams/${teamSlug(team)}/`;
export const gameSlug=(game:GameRouteLike)=>`${slugify(game.awayName)}-${game.neutral?'vs':'at'}-${slugify(game.homeName)}-${game.id}`;
export const gamePath=(game:GameRouteLike)=>`/games/${game.season}/${gameSlug(game)}/`;
