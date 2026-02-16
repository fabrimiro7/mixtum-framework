import { Component, OnInit } from '@angular/core';

interface SideNavToggle {
  screenWidth: number;
  collapsed: boolean;
}

@Component({
  selector: 'app-full-width',
  templateUrl: './full-width.component.html',
  styleUrls: ['./full-width.component.css']
})
export class FullWidthComponent implements OnInit {

  isSideNavCollapsed = false;
  screenWidth = 0;

  constructor() { }

  ngOnInit(): void {
  }

  onToggleSideNav(data: SideNavToggle): void {
    this.screenWidth = data.screenWidth;
    this.isSideNavCollapsed = data.collapsed;
  }

}
