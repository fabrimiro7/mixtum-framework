export class Message {

    id: number | any;
    text: string | any;
    ticket: number | any;
    author: number | any;
    insert_date: string | any;
    attachments: any;
  

    constructor(
        text: string | any,
    ){
        this.text = text;
    }
}