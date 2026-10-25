from pathlib import Path
import json
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
shots=root/'screenshots'
shots.mkdir(exist_ok=True)
checks=[]
def check(name,value):
    assert value,name
    checks.append(name)
    print('PASS:',name,flush=True)
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1280,'height':1000})
    errors=[]; requests=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.on('request',lambda r: requests.append(r.url))
    page.add_init_script('let seed=42; Math.random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296}')
    page.goto((root/'index.html').as_uri())
    page.wait_for_timeout(300)
    check('World renders with no JavaScript errors',page.evaluate("mode==='world'") and not errors)
    page.screenshot(path=str(shots/'village.png'),full_page=True)
    check('License starts locked',page.locator('#license').is_disabled())
    moving=page.evaluate('residents[0].x');page.wait_for_timeout(250)
    check('Village residents wander',page.evaluate('residents[0].x')!=moving)
    page.evaluate('hero.x=480;hero.y=146')
    page.keyboard.press('e');page.locator('#overlay').wait_for(state='visible')
    check('Forest gate explains license requirement',page.get_by_role('heading',name='A license to venture further.').is_visible())
    check('No enter-forest option before victory',page.get_by_role('button',name='Enter the forest',exact=True).count()==0)
    page.evaluate('enterForest()')
    check('Forest entry function enforces license',page.evaluate("region==='village'"))
    page.get_by_role('button',name='Find Rowan',exact=True).click()
    page.evaluate('hero.x=residents[0].x+10;hero.y=residents[0].y+10')
    page.keyboard.press('e');page.locator('#overlay').wait_for(state='visible')
    check('Villager offers quest dialogue','MIRA' in page.locator('#dialog-label').inner_text())
    page.get_by_role('button',name='Back to exploring',exact=True).click()
    page.evaluate('hero.x=residents[2].x+5;hero.y=residents[2].y+5')
    page.keyboard.press('e');page.wait_for_timeout(100)
    check('Village cat reacts to interaction','Pip' in page.locator('#hint').inner_text() and page.locator('#overlay').is_hidden())
    page.evaluate('hero.x=365;hero.y=385')
    page.keyboard.down('d');page.wait_for_function('hero.x>=610');page.keyboard.up('d')
    page.keyboard.down('w');page.wait_for_function('hero.y<=255');page.keyboard.up('w')
    page.keyboard.press('e')
    page.locator('#overlay').wait_for(state='visible')
    check('Walk to Rowan and open dialogue by keyboard',page.locator('#overlay').is_visible())
    page.get_by_role('button',name='Accept the challenge').click()
    page.wait_for_function('countdown<=0')
    check('Accepting challenge begins live duel',page.evaluate("mode==='fight' && countdown<=0"))
    check('Duel spawns clear of solid crates',page.evaluate('![player,enemy].some(f=>platforms.some(p=>overPlatform(f,p)&&f.y>p.y))'))
    page.keyboard.down('d');page.wait_for_function('Math.abs(player.x-enemy.x)<70');page.keyboard.up('d')
    page.wait_for_function('Math.abs(player.y-enemy.y)<40')
    hp=page.evaluate('enemy.hp')
    for i in range(4):
        page.keyboard.press('j');page.wait_for_timeout(550)
    check('Keyboard attacks damage opponent',page.evaluate('enemy.hp')<hp)
    check('Opponent AI approaches and attacks',page.evaluate('player.hp<100'))
    page.keyboard.press('Escape')
    check('Escape pauses and opens pause dialog',page.evaluate('paused') and page.locator('#overlay').is_visible())
    timer=page.evaluate('roundTime');page.wait_for_timeout(300)
    check('Pause freezes combat timer',page.evaluate('roundTime')==timer)
    page.get_by_role('button',name='Resume',exact=True).click()
    check('Resume returns keyboard focus to game',page.evaluate("!paused && document.activeElement===canvas"))
    page.wait_for_function('!player.action && player.stun<=0')
    page.keyboard.down('l');page.wait_for_timeout(100)
    check('Guard keyboard input works',page.evaluate('player.block'))
    page.keyboard.up('l');page.wait_for_timeout(100)
    # Isolate mechanics to exercise exact combat boundaries reproducibly.
    report=page.evaluate('''() => {
      paused=true;
      const a=fighter(320,'green',1), b=fighter(385,'gold',-1);
      attack(a); a.action.age=.15; hit(a,b); const strike=b.hp===90;
      hit(a,b); const singleHit=b.hp===90;
      a.action=null;a.cool=0;attack(a,true);a.action.age=.47;b.block=true;b.st=100;hit(a,b);
      const guard=b.hp===85 && b.st===75;
      a.action=null;a.cool=0;a.st=0;attack(a,true);const stamina=!a.action;
      a.st=100;attack(a);a.action.age=.15;b.block=false;b.y=330;hit(a,b);const jump=b.hp===85;
      tickFighter(b,.1);const regen=b.st>75;
      player=fighter(320,'#9ed5c2',1);enemy=fighter(385,'#ddab69',-1);paused=false;
      return {strike,singleHit,guard,stamina,jump,regen};
    }''')
    for name,ok in report.items():check('Combat mechanic: '+name,ok)
    page.keyboard.press('Space');page.wait_for_timeout(120)
    check('Space triggers jump',page.evaluate('player.y<440'))
    page.screenshot(path=str(shots/'duel.png'),full_page=True)
    # Solid crate physics, grounded input, and AI traversal.
    physics=page.evaluate('''() => {
      paused=true;
      const f=fighter(140,'green',1),p=platforms[0];
      moveFighter(f,50);const wall=f.x===p.x-FIGHT_RADIUS;
      f.vy=-JUMP_SPEED;
      for(let i=0;i<100;i++){tickFighter(f,.01);if(i<55)moveFighter(f,1.5)}
      const landed=Math.abs(f.y-p.y)<.01&&isGrounded(f);
      const startY=f.y;f.vy=-JUMP_SPEED;tickFighter(f,.02);
      const rejump=f.y<startY;
      f.x=p.x+p.w/2;f.y=p.y;f.vy=0;moveFighter(f,150);
      for(let i=0;i<90;i++)tickFighter(f,.01);
      const stepOff=f.y===FIGHT_GROUND&&isGrounded(f);
      const a=fighter(480,'green',1);a.y=344;a.vy=0;
      const b=fighter(550,'gold',-1);attack(a);a.action.age=.15;hit(a,b);
      const separation=b.hp===100;
      player=fighter(320,'#9ed5c2',1);enemy=fighter(390,'#ddab69',-1);countdown=0;clearInput();
      const allTops=platforms.every(platform=>{
        const z=fighter(platform.x+platform.w/2,'green',1);z.y=platform.y-50;z.vy=100;
        for(let i=0;i<80;i++)tickFighter(z,.01);
        return Math.abs(z.y-platform.y)<.01&&isGrounded(z);
      });
      return {wall,landed,rejump,stepOff,separation,allTops};
    }''')
    for name,ok in physics.items():check('Platform mechanic: '+name,ok)
    page.evaluate("player.x=480;player.y=344;player.vy=0;enemy.x=580;enemy.face=-1;enemy.cool=0;paused=false")
    page.wait_for_function('enemy.vy<0 || enemy.y<440')
    check('Rowan jumps toward elevated player',page.evaluate('enemy.vy<0 || enemy.y<440'))
    page.evaluate("paused=true;player.x=225;player.y=380;player.vy=0;player.action=null;player.stun=0;enemy.x=820;enemy.y=440;enemy.vy=0;texts=[];particles=[]")
    page.screenshot(path=str(shots/'platforms.png'),full_page=True)
    page.evaluate('paused=false')
    page.keyboard.down('l');page.wait_for_timeout(100)
    check('Guard works while standing on a crate',page.evaluate('player.block'))
    page.keyboard.up('l');page.wait_for_timeout(50)
    page.keyboard.press('Space');page.wait_for_timeout(100)
    check('Keyboard can jump from a crate',page.evaluate('player.y<380'))
    vy=page.evaluate('player.vy');page.keyboard.press('Space');page.wait_for_timeout(70)
    check('Jump cannot reset in midair',page.evaluate('player.vy')>vy)
    page.evaluate("enemy.hp=0; result()")
    check('Victory offers rematch and village return',page.get_by_role('heading',name='The clearing has a new champion.').is_visible())
    check('Victory grants signed forest license',page.evaluate('licensed') and page.locator('#license-card').is_visible())
    page.screenshot(path=str(shots/'license.png'),full_page=True)
    page.get_by_role('button',name='Rematch',exact=True).click()
    check('Rematch resets health, stamina, timer',page.evaluate('player.hp===100 && enemy.hp===100 && player.st===100 && roundTime===90'))
    page.evaluate('player.hp=0;result()')
    check('Defeat offers retry',page.get_by_role('heading',name='Every guardian started somewhere.').is_visible())
    page.get_by_role('button',name='Return to village',exact=True).click()
    check('Return to village preserves session score',page.evaluate("mode==='world' && wins===1 && losses===1"))
    check('Later defeat does not revoke earned license',page.evaluate('licensed'))
    page.keyboard.press('i');page.locator('#license-card').wait_for(state='visible')
    check('Inventory hotkey displays earned license',page.locator('#license-card').is_visible())
    page.get_by_role('button',name='Continue exploring',exact=True).click()
    page.evaluate('hero.x=480;hero.y=146')
    page.keyboard.press('e');page.locator('#overlay').wait_for(state='visible')
    page.get_by_role('button',name='Enter the forest',exact=True).click()
    check('Licensed gate leads into forest',page.evaluate("region==='forest' && mode==='world'"))
    page.screenshot(path=str(shots/'forest.png'),full_page=True)
    page.evaluate('hero.x=woodland[0].x+10;hero.y=woodland[0].y+10')
    page.keyboard.press('e');page.wait_for_timeout(100)
    check('Forest wildlife reacts to player','Fern' in page.locator('#hint').inner_text())
    page.evaluate('hero.x=swordStone.x;hero.y=swordStone.y+45')
    page.keyboard.press('e');page.locator('#overlay').wait_for(state='visible')
    check('Forest sword opens interaction prompt',page.get_by_role('button',name='Pull the sword',exact=True).is_visible())
    page.get_by_role('button',name='Leave it for now',exact=True).click()
    check('Declining leaves sword unclaimed',page.evaluate("!swordOwned && mode==='world'"))
    page.keyboard.press('e');page.locator('#overlay').wait_for(state='visible')
    page.get_by_role('button',name='Pull the sword',exact=True).click()
    check('Pull action begins cutscene',page.evaluate("mode==='cutscene' && !swordOwned"))
    page.wait_for_function('cutscene && cutscene.elapsed>1.5')
    page.keyboard.down('d');page.wait_for_timeout(100);page.keyboard.up('d')
    check('Movement is locked during cutscene',page.evaluate('Math.abs(hero.x-swordStone.x)<1'))
    page.keyboard.press('Escape')
    t=page.evaluate('cutscene.elapsed');page.wait_for_timeout(200)
    check('Pause freezes sword cutscene',page.evaluate('cutscene.elapsed')==t)
    page.get_by_role('button',name='Resume',exact=True).click()
    page.wait_for_function('cutscene && cutscene.elapsed>4.3')
    page.screenshot(path=str(shots/'sword-cutscene.png'),full_page=True)
    page.wait_for_function("mode==='world' && swordOwned")
    check('Full cutscene awards sword',page.get_by_role('heading',name='Mosslight awakens.').is_visible())
    page.get_by_role('button',name='Continue exploring',exact=True).click()
    page.get_by_role('button',name='Mosslight sword',exact=True).click()
    check('Claimed sword has inspectable inventory entry',page.get_by_role('heading',name='Mosslight, the forest blade.').is_visible())
    page.get_by_role('button',name='Continue exploring',exact=True).click()
    page.keyboard.press('e');page.locator('#overlay').wait_for(state='visible')
    check('Sword cannot be claimed twice',page.get_by_role('heading',name='Only a quiet stone remains.').is_visible())
    page.get_by_role('button',name='Continue exploring',exact=True).click()
    page.evaluate('hero.x=480;hero.y=485')
    page.keyboard.press('e');page.wait_for_function("region==='village'")
    check('South trail returns to village with sword',page.evaluate('licensed && swordOwned'))
    # Controlled result states cover loss and draw without granting a license.
    page.evaluate('licensed=false;startFight();player.hp=0;result()')
    check('Defeat cannot grant first license',page.evaluate('!licensed') and page.locator('#license-card').is_hidden())
    page.get_by_role('button',name='Rematch',exact=True).click()
    page.evaluate('roundTime=0;player.hp=50;enemy.hp=50;result()')
    check('Draw cannot grant first license',page.evaluate('!licensed') and page.locator('#license-card').is_hidden())
    page.get_by_role('button',name='Rematch',exact=True).click()
    page.evaluate('roundTime=0;player.hp=80;enemy.hp=30;result()')
    check('Timer victory also awards license',page.evaluate('licensed') and page.locator('#license-card').is_visible())
    page.get_by_role('button',name='Return to village',exact=True).click()
    page.set_viewport_size({'width':390,'height':844})
    page.wait_for_timeout(100)
    check('Mobile layout fits viewport',page.evaluate('document.documentElement.scrollWidth<=390'))
    before=page.evaluate('hero.x')
    button=page.get_by_role('button',name='Move left',exact=True)
    box=button.bounding_box()
    page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
    page.mouse.down()
    page.wait_for_timeout(150)
    page.mouse.up()
    check('On-screen movement control works',page.evaluate('hero.x')<before)
    page.screenshot(path=str(shots/'mobile.png'),full_page=True)
    page.get_by_role('button',name='Forest license',exact=True).click()
    check('Mobile license card is accessible',page.locator('#license-card').is_visible())
    check('Mobile dialog actions fit viewport',page.locator('#dialog-actions button').evaluate('(b)=>{const r=b.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight}'))
    page.screenshot(path=str(shots/'mobile-license.png'),full_page=True)
    page.get_by_role('button',name='Continue exploring',exact=True).click()
    # Test skip and on-screen interaction at mobile width with a fresh claim state.
    page.evaluate("swordOwned=false;region='forest';hero.x=swordStone.x;hero.y=swordStone.y+45;refreshWorldUI()")
    b=page.get_by_role('button',name='Talk',exact=True);box=b.bounding_box()
    page.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2)
    page.locator('#overlay').wait_for(state='visible')
    page.get_by_role('button',name='Pull the sword',exact=True).click()
    check('Mobile cutscene has accessible skip control',page.get_by_role('button',name='Skip cutscene',exact=True).is_visible())
    page.get_by_role('button',name='Skip cutscene',exact=True).click()
    check('Skipping cleanly completes acquisition',page.evaluate("swordOwned && mode==='world' && !cutscene") and page.locator('#cinematic').is_hidden())
    page.get_by_role('button',name='Continue exploring',exact=True).click()
    page.reload();page.wait_for_timeout(150)
    check('Refresh resets visit-only license and sword',page.evaluate('!licensed && !swordOwned') and page.locator('#license').is_disabled())
    check('No runtime JavaScript errors',not errors)
    check('No HTTP or API requests',not any(u.startswith(('http:','https:','ws:','wss:')) for u in requests))
    browser.close()
print(json.dumps({'passed':len(checks),'screenshots':str(shots)},indent=2))
