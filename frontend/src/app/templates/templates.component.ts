import { InMemoryCache } from 'apollo-cache-inmemory';
import { Component, OnInit } from '@angular/core';
import { TeplatesService } from './templates.service';
import { map,filter } from 'rxjs/operators';

@Component({
  selector: 'vdi-templates',
  templateUrl: './templates.component.html',
  styleUrls: ['./templates.component.scss']
})
export class TemplatesComponent implements OnInit {

  public infoTeplates: [];

  constructor(private service: TeplatesService){}

  ngOnInit() {
    this.getAllTeplates();
  }

  private getAllTeplates() {
    this.service.getAllTeplates().valueChanges.pipe(map(data => data.data.templates))
      .subscribe( (data) => {
        this.infoTeplates = data;
        console.log(data);
      });
  }




}
