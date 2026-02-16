export class User {

  id: number;
  first_name: string;
  last_name: string;
  fiscal_code: string;
  phone: string;
  avatar: string;
  username: string;
  email: string;
  
  constructor(
    id: number,
    first_name: string,
    last_name: string,
    fiscal_code: string,
    phone: string,
    avatar: string,
    username: string,
    email: string,
  ) {
    this.id = id;
    this.first_name = first_name;
    this.last_name = last_name;
    this.fiscal_code = fiscal_code;
    this.phone = phone;
    this.avatar = avatar;
    this.username = username;
    this.email = email;
  }
}