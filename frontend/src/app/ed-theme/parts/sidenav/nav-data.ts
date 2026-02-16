import { INavbarData } from "./helper";

export const navbarDataSuperAdmin: INavbarData[] = [
    {
        routeLink: 'dashboard',
        icon: 'dashboard',
        label: 'Dashboard'
    },
    {
        routeLink: 'tickets',
        icon: 'headset_mic',
        label: 'Tickets'
    },
    /*{
        routeLink: 'meeting',
        icon: 'calendar_month',
        label: 'Riunioni'
    },*/
    {
        routeLink: 'payments',
        icon: 'payments',
        label: 'Abbonamenti'
    },
    {
        routeLink: 'projects',
        icon: 'wysiwyg',
        label: 'Progetti'
    },
    {
        routeLink: 'documents',
        icon: 'description',
        label: 'Documenti',
        items: [
            { icon: 'description', routeLink: '/documents', label: 'Documenti' },
            { icon: 'view_list', routeLink: '/documents/templates', label: 'Template' },
        ]
    },
    {
        routeLink: 'finance',
        icon: 'account_balance',
        label: 'Finance',
        items: [
            { icon: 'receipt_long', routeLink: '/finance', label: 'Movimenti' },
            { icon: 'bar_chart', routeLink: '/finance/chart', label: 'Grafici' },
            { icon: 'trending_up', routeLink: '/finance/simulation', label: 'Simulazione' },
            { icon: 'account_balance', routeLink: '/finance/accounts', label: 'Banche e Conti' },
            { icon: 'repeat', routeLink: '/finance/recurring', label: 'Movimenti Ricorrenti' },
        ]
    },
    {
        routeLink: 'academy',
        icon: 'video_library',
        label: 'Tutorial'
    },
    {
        routeLink: 'profile',
        icon: 'account_circle',
        label: 'Profilo'
    },
    {
        routeLink: 'settings',
        icon: 'settings',
        label: 'Impostazioni',
        items: [
            {
                icon: 'settings',
                routeLink: 'usermanager/users-list',
                label: 'Gestione utenti',
            },
        ]
    },
];

export const navbarDataAdmin: INavbarData[] = [
    {
        routeLink: 'dashboard',
        icon: 'dashboard',
        label: 'Dashboard'
    },
    {
        routeLink: 'tickets',
        icon: 'headset_mic',
        label: 'Tickets'
    },
    /*{
        routeLink: 'meeting',
        icon: 'calendar_month',
        label: 'Riunioni'
    },*/
    {
        routeLink: 'payments',
        icon: 'payments',
        label: 'Abbonamenti'
    },
    {
        routeLink: 'projects',
        icon: 'wysiwyg',
        label: 'Progetti'
    },
    {
        routeLink: 'documents',
        icon: 'description',
        label: 'Documenti',
        items: [
            { icon: 'description', routeLink: '/documents', label: 'Documenti' },
            { icon: 'view_list', routeLink: '/documents/templates', label: 'Template' },
        ]
    },
    {
        routeLink: 'academy',
        icon: 'video_library',
        label: 'Tutorial'
    },
    {
        routeLink: 'profile',
        icon: 'account_circle',
        label: 'Profilo'
    },
    {
        routeLink: 'settings',
        icon: 'settings',
        label: 'Impostazioni',
        items: [
            {
                icon: 'settings',
                routeLink: 'usermanager/users-list',
                label: 'Gestione utenti',
            },
            {
                routeLink: 'customizer',
                label: 'Personalizza',
            }
        ]
    },
];

export const navbarDataUser: INavbarData[] = [
    {
        routeLink: 'dashboard',
        icon: 'dashboard',
        label: 'Dashboard'
    },
    {
        routeLink: 'tickets',
        icon: 'headset_mic',
        label: 'Tickets'
    },
    /*{
        routeLink: 'meeting',
        icon: 'calendar_month',
        label: 'Riunioni'
    },*/
    {
        routeLink: 'projects',
        icon: 'wysiwyg',
        label: 'Progetti'
    },
    {
        routeLink: 'payments',
        icon: 'payments',
        label: 'Abbonamenti'
    },
    {
        routeLink: 'academy',
        icon: 'video_library',
        label: 'Tutorial'
    },
    {
        routeLink: 'profile',
        icon: 'account_circle',
        label: 'Profilo'
    },
];

export const navbarDataEmployee: INavbarData[] = [
    {
        routeLink: 'dashboard',
        icon: 'dashboard',
        label: 'Dashboard'
    },
    {
        routeLink: 'tickets',
        icon: 'headset_mic',
        label: 'Tickets'
    },
    /*{
        routeLink: 'meeting',
        icon: 'calendar_month',
        label: 'Riunioni'
    },
    {
        routeLink: 'payments',
        icon: 'payments',
        label: 'Abbonamenti'
    },*/
    {
        routeLink: 'academy',
        icon: 'video_library',
        label: 'Tutorial'
    },
    {
        routeLink: 'profile',
        icon: 'account_circle',
        label: 'Profilo'
    },
];
