import { Component, OnInit } from '@angular/core';
import { FooterService } from './footer.service';

interface iCountEvents {
  warning: number;
  error: number;
  count: number;
}

@Component({
  selector: 'vdi-footer',
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.scss']
})
export class FooterComponent implements OnInit {

  info: any = {};
  license: any = {};

  openedLog: boolean = false;
  log: string = '';

  countEvents: iCountEvents;


  constructor(private service: FooterService) { }

  ngOnInit() {
    this.service.getInfo().subscribe((res) => {
      this.info = res.data;
    });

    this.getLicense();

    this.service.channel$.subscribe(() => {
      this.getLicense();
    })

    this.service.countEvents().valueChanges.subscribe(res => {
      console.log(res)
      this.countEvents = res.data;
    })
  }

  openLog(log) {
    if (log !== this.log) {
      this.openedLog = false;
      this.log = log;

      setTimeout(() => {
        this.openedLog = true;
      })
    } else {
      this.closeLog();
    }
  }

  closeLog() {
    this.log = '';
    this.openedLog = false;
  }

 
  getLicense() {
    this.service.getLicence().subscribe((res) => {
      this.license = res.data;
    });
  }

}
