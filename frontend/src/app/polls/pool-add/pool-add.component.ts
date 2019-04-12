import { Component, OnInit } from '@angular/core';
import { PoolsService } from './../polls.service';
import { map } from 'rxjs/operators';

@Component({
  selector: 'vdi-pool-add',
  templateUrl: './pool-add.component.html',
  styleUrls: ['./pool-add.component.scss']
})

export class PoolAddComponent implements OnInit {

  public options: object[];
  private tmId: string;
  public la:string;

  constructor(private poolsService: PoolsService) {
  }

  ngOnInit() {
    this.getTemplate();
  }

  private getTemplate() {
    this.poolsService.getAllTemplates().valueChanges.pipe(map(data => data.data.templates)).subscribe((res)=> {
      this.options = res.map((item) => {
        return {
          'output': item.id,
          'input': item.name
        }
      })
    });
  }

  private selectValue(data) {
    this.tmId = data[0];
    console.log(data);
  }

  public send() {
    this.poolsService.createPoll(this.la,this.tmId).subscribe((res) => {
      if(res) {
        this.poolsService.getAllPools().valueChanges.subscribe();
      }

    });
  }

}
