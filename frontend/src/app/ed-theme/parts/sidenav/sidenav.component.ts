import { animate, keyframes, style, transition, trigger } from '@angular/animations';
import { Component, Output, EventEmitter, OnInit, HostListener, Inject, Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { fadeInOut, INavbarData } from './helper';
import { navbarDataSuperAdmin, navbarDataAdmin, navbarDataUser, navbarDataEmployee } from './nav-data';
import { PermissionService } from 'src/app/services/auth/permission.service';
import { CookieService } from 'ngx-cookie-service';
import { ButtonClickService } from 'src/app/services/utils/button-click.service';
import { BrandingService } from 'src/app/services/theme/branding.service';

interface SideNavToggle {
  screenWidth: number;
  collapsed: boolean;
}

@Component({
  selector: 'app-sidenav',
  templateUrl: './sidenav.component.html',
  styleUrls: ['../../../../styles.css', './sidenav.component.scss', ],
  animations: [
    fadeInOut,
    trigger('rotate', [
      transition(':enter', [
        animate('1000ms', 
          keyframes([
            style({transform: 'rotate(0deg)', offset: '0'}),
            style({transform: 'rotate(2turn)', offset: '1'})
          ])
        )
      ])
    ])
  ]
})
@Injectable()
export class SidenavComponent implements OnInit {

  @Output() onToggleSideNav: EventEmitter<SideNavToggle> = new EventEmitter();
  collapsed = false;
  screenWidth = 0;
  navData: any = undefined;
  multiple: boolean = false;
  logoFullUrl = 'assets/img/logo-esteso.png';
  logoCompactUrl = 'assets/img/logo-compatto.png';

  @HostListener('window:resize', ['$event'])
  onResize(event: any) {
    this.screenWidth = window.innerWidth;
    if(this.screenWidth <= 768 ) {
      this.collapsed = false;
      this.onToggleSideNav.emit({collapsed: this.collapsed, screenWidth: this.screenWidth});
    }
  }

  constructor(
    private router: Router,
    private permission: PermissionService,
    private cookieService: CookieService,
    private buttonClickService: ButtonClickService,
    private brandingService: BrandingService,
    ) {}

  ngOnInit(): void {
      this.screenWidth = window.innerWidth;
      var permission = this.permission.checkPermission(this.cookieService.get('token'))
      if (permission == 'SuperAdmin')
      {
        this.navData = navbarDataSuperAdmin;
      } else if (permission == 'Admin') {
        this.navData = navbarDataAdmin;
      } else if (permission == 'Utente') {
        this.navData = navbarDataUser;
      } else if (permission == 'Employee') {
        this.navData = navbarDataEmployee;
      }

      this.brandingService.branding$.subscribe((branding) => {
        this.logoFullUrl = branding?.logo_full || 'assets/img/logo-esteso.png';
        this.logoCompactUrl = branding?.logo_compact || 'assets/img/logo-compatto.png';
      });
  }

  toggleCollapse(expand: boolean = false): void {
    this.collapsed = expand ? false : !this.collapsed;
    this.onToggleSideNav.emit({ collapsed: this.collapsed, screenWidth: this.screenWidth });
  }

  closeSidenav(): void {
    this.collapsed = false;
    this.onToggleSideNav.emit({collapsed: this.collapsed, screenWidth: this.screenWidth});
  }

  handleClick(item: INavbarData): void {
    if (this.collapsed) {
      if (this.screenWidth <= 768 && !item.items?.length) {
        this.collapsed = false;
      } else {
        this.collapsed = true;
      }
      this.onToggleSideNav.emit({ collapsed: this.collapsed, screenWidth: this.screenWidth });
      setTimeout(() => {
        item.expanded = true;  
      }, 300); 
    } else {
      this.shrinkItems(item);
      item.expanded = !item.expanded;
      this.toggleCollapse()
    }
  }

  getActiveClass(data: INavbarData): string {
    return this.router.url.includes(data.routeLink) ? 'active' : '';
  }

  shrinkItems(item: INavbarData): void {
    if (!this.multiple) {
      for(let modelItem of this.navData) {
        if (item !== modelItem && modelItem.expanded) {
          modelItem.expanded = false;
        }
      }
    }
    
    // Chiudi la sidenav solo se è un elemento senza figli (figlio) e siamo su mobile
    if (this.screenWidth <= 768 && !item.items?.length) {
      setTimeout(() => {
        this.closeSidenav();
      }, 300);
    }
  }
  

  buttonClick() {
    this.buttonClickService.clickButton();
  }
}
