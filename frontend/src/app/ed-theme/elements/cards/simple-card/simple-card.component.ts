import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'app-simple-card',
  templateUrl: './simple-card.component.html',
  styleUrls: ['./simple-card.component.css']
})
export class SimpleCardComponent implements OnInit {

  @Input() cardTitle: string = '';
  @Input() cardDescription: string = '';

  constructor() { }

  ngOnInit(): void {
  }

}
