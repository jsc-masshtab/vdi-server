import { Component, OnInit } from '@angular/core';
import { PoolsService } from './../polls.service';
import { map } from 'rxjs/operators';

@Component({
  selector: 'vdi-pool-add',
  templateUrl: './pool-add.component.html',
  styleUrls: ['./pool-add.component.scss']
})
export class PoolAddComponent implements OnInit {

  constructor(private poolsService: PoolsService) {}

  ngOnInit() {
    this.getTemplate();
  }

  private getTemplate() {
    this.poolsService.getAllTemplates().valueChanges.pipe(map(data => data.data.templates)).subscribe((res)=> {
      console.log(res);
    });
  }

}
