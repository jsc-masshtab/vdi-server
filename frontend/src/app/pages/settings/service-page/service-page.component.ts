import { Component, OnInit } from '@angular/core';

import { ServicePageService } from './service-page.service';

@Component({
  selector: 'vdi-service-page',
  templateUrl: './service-page.component.html',
  styleUrls: ['./service-page.component.scss']
})
export class ServicePageComponent implements OnInit {

  constructor(private servicePageService: ServicePageService) { }

  public ngOnInit(): void {
    this.servicePageService.getServicesInfo().valueChanges.subscribe((res: any) => {
      console.log(res); 
    })
  }

}
