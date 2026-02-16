import { Project } from "./project";
import { User } from "./user";

export class Tutorial {

    constructor(
        public id: number | any,
        public title: string | any,
        public description: string | any,
        public link: string | any,
        public projects: Project | any,
        public duration: number | any,
        public level: string | any,
        public author: User | any,
        public category: string | any,

    ){}
}