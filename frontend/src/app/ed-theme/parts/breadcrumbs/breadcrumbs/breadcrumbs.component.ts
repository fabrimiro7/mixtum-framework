import { Component, OnInit } from '@angular/core';
import { BreadcrumbsService } from '../breadcrumbs.service';

@Component({
  selector: 'app-breadcrumbs',
  templateUrl: './breadcrumbs.component.html',
  styleUrls: ['./breadcrumbs.component.css']
})
export class BreadcrumbsComponent implements OnInit {
  breadcrumbs: Array<{ label: string, url: string }> = [];

  constructor(private breadcrumbsService: BreadcrumbsService) {}

  ngOnInit() {
    this.breadcrumbsService.breadcrumbs.subscribe(breadcrumbs => {
      this.breadcrumbs = breadcrumbs;
    });
  }
}
